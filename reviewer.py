import asyncio
import json as sys_json
from typing import Any, List, Literal, Optional, Union

from aiohttp import ClientConnectorError
from aiotieba import Account, Client, PostSortType
from aiotieba.typing import Comment, Comments, Post, Posts, Thread, Threads
from pydantic import BaseModel
from sanic.log import logger

from custom_type import ApiType, App
from models import Post as PostRecord
from models import Thread as ThreadRecord
from utils import union_ws_send


class Reviewer:
    def __init__(
        self,
        app: App,
        fname_list: List[str],
        max_request: int = 8,
        wait_time: int = 30,
        account: Account = Account(),
    ):
        """
        Attributes:
            - app: App对象，类型为App
            - fname_list: 贴吧名列表，类型为List[str]
            - max_request: 最大并发请求量，默认值为8，类型为int
            - wait_time: 最长等待时间，默认值为30秒，类型为int
            - account: 账户信息，默认为Account类的一个实例，类型为Account
        """
        self.app = app
        self.client = Client(account=account)
        self.semaphore = asyncio.Semaphore(max_request)
        self.fname_list = fname_list
        self.wait_time = wait_time

    async def start_review(self):
        count = 0
        async with self.client:
            while True:
                for fname in self.fname_list:
                    try:
                        await self.check_threads(fname)
                    except Exception as e:
                        logger.warning(e)
                    await asyncio.sleep(3)

                count += 1
                logger.debug(
                    "The %dth review loop has ended, waiting for %d seconds before the next loop.",
                    count,
                    self.wait_time,
                )
                await asyncio.sleep(self.wait_time)

    async def check_threads(self, fname: str):
        """
        检查主题贴的内容
        Args:
            client: 传入了执行账号的贴吧客户端
            fname: 贴吧名

        """
        async with self.semaphore:
            first_threads: Threads = await self.client.get_threads(fname)

        will_check_child: List[Thread] = []

        async def check_last_time(_thread: Thread):
            if _thread.is_livepost:
                return None
            prev_thread = await ThreadRecord.filter(tid=_thread.tid).get_or_none()
            if prev_thread:
                if _thread.last_time < prev_thread.last_time:
                    await ThreadRecord.filter(tid=_thread.tid).update(
                        last_time=_thread.last_time
                    )
                elif _thread.last_time > prev_thread.last_time:
                    will_check_child.append(_thread)
                    await ThreadRecord.filter(tid=_thread.tid).update(
                        last_time=_thread.last_time
                    )
            else:
                self.send_to(_thread, "thread")

                will_check_child.append(_thread)
                await ThreadRecord.create(
                    tid=_thread.tid,
                    fid=await self.client.get_fid(fname),
                    last_time=_thread.last_time,
                )

        await asyncio.gather(*[check_last_time(thread) for thread in first_threads])

        await asyncio.gather(*[
            self.check_posts(thread.tid) for thread in will_check_child
        ])

    async def check_posts(self, tid: int):
        """
        检查楼层内容
        Args:
            client: 传入了执行账号的贴吧客户端
            tid: 所在主题贴id
        """
        async with self.semaphore:
            last_posts: Posts = await self.client.get_posts(
                tid,
                pn=0xFFFF,
                sort=PostSortType.DESC,
                with_comments=True,
                comment_rn=10,
            )

        if last_posts and last_posts[-1].floor != 1:
            last_floor = last_posts[0].floor
            need_rn = last_floor - len(last_posts)
            if need_rn > 0:
                post_set = set(last_posts.objs)
                rn_clamp = 30
                if need_rn <= rn_clamp:
                    async with self.semaphore:
                        first_posts = await self.client.get_posts(
                            tid, rn=need_rn, with_comments=True, comment_rn=10
                        )

                    post_set.update(first_posts.objs)
                else:
                    async with self.semaphore:
                        first_posts = await self.client.get_posts(
                            tid, rn=rn_clamp, with_comments=True, comment_rn=10
                        )

                    post_set.update(first_posts.objs)

                    async with self.semaphore:
                        hot_posts = await self.client.get_posts(
                            tid,
                            sort=PostSortType.HOT,
                            with_comments=True,
                            comment_rn=10,
                        )

                    post_set.update(hot_posts.objs)
                posts = list(post_set)
            else:
                posts = last_posts.objs
        else:
            posts = last_posts.objs

        will_check_child: List[Post] = []

        async def check_reply_num(_post: Post):
            prev_post = await PostRecord.filter(pid=_post.pid).get_or_none()
            if prev_post:
                if _post.reply_num < prev_post.reply_num:
                    await PostRecord.filter(pid=_post.pid).update(
                        reply_num=_post.reply_num
                    )
                elif _post.reply_num > prev_post.reply_num:
                    will_check_child.append(_post)
                    await PostRecord.filter(pid=_post.pid).update(
                        reply_num=_post.reply_num
                    )
            else:
                self.send_to(_post, "post")

                will_check_child.append(_post)
                await PostRecord.create(
                    pid=_post.pid, tid=tid, reply_num=_post.reply_num
                )

        await asyncio.gather(*[check_reply_num(post) for post in posts])

        await asyncio.gather(*[self.check_comment(post) for post in will_check_child])

    async def check_comment(self, post: Post):
        """
        检查楼中楼内容
        Args:
            client: 传入了执行账号的贴吧客户端
            post: 楼层
        """

        if post.reply_num > 10 or (
            len(post.comments) != post.reply_num and post.reply_num <= 10
        ):
            async with self.semaphore:
                last_comments: Comments = await self.client.get_comments(
                    post.tid, post.pid, pn=post.reply_num // 30 + 1
                )

            comment_set = set(post.comments)
            comment_set.update(last_comments.objs)
            comments = list(comment_set)
        else:
            comments = post.comments

        async def check_comment_of_db(_comment: Comment):
            prev_comment = await PostRecord.filter(pid=_comment.pid).get_or_none()
            if not prev_comment:
                self.send_to(_comment, "comment")

                await PostRecord.create(
                    pid=_comment.pid, tid=_comment.tid, ppid=post.pid
                )

        await asyncio.gather(*[check_comment_of_db(comment) for comment in comments])

    def send_to(self, context: Union[Thread, Post, Comment], ctx_type: str = "unknown"):
        result = PushMessage(
            push_type="message",
            msg_type=ctx_type,
            data=context,
        ).model_dump(exclude_none=True)
        result = sys_json.dumps(result)

        logger.debug("send %s", result)

        for ws in self.app.ctx.ws_connections:
            self.app.add_task(union_ws_send(ws, result))

        for http_url in self.app.ctx.config.http_callback_url:
            self.app.add_task(self._post_send(http_url, result))
    
    async def _post_send(self, url: str, data):
        try:
            await self.app.ctx.http_session.post(url, json=data)
        except ClientConnectorError:
            logger.warning("post send to %s failed", url)


class PushMessage(BaseModel):
    push_type: Literal["message", "event"]
    msg_type: Optional[Literal["thread", "post", "comment"]] = None
    event_type: Optional[str] = None
    data: Any = None


def create_reviewers(app: App):
    if (
        ApiType.WS in app.config.API_TYPE
        or ApiType.HTTP_CALLBACK in app.config.API_TYPE
        or ApiType.REVERSE_WS in app.config.API_TYPE
    ):
        task = app.add_task(
            Reviewer(app, app.ctx.config.fnames).start_review(),
            name="reviewer",
        )
        logger.info("Reviewer task %s was created.", task.get_name())
        return task

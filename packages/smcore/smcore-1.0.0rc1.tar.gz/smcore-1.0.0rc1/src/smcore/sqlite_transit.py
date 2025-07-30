import os
import sqlite3
from . import core
from .hardcore_post import Post

# SQLite transit is built on top of hardcore posts
#
# I haven't vetted this for security, in particular SQL injections.  I've tried
# my best to follow the advice given in the docs for sqlite3.


class SQLiteTransit(core.Blackboard):
    def __init__(self, path: str):
        self._name = "sqlite-transit"
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()

        # provision the db if needed
        # "index" is "id" since index is a keyword
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS posts(
                idx INTEGER PRIMARY KEY,
                source TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                data TEXT,
                encryption TEXT DEFAULT 'aes-gcm'
            );
            """)
        self.con.commit()

        self.cur.execute("CREATE TABLE IF NOT EXISTS tags(tag TEXT UNIQUE);")
        self.con.commit()

        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS post_tags(post INTEGER, tag TEXT, FOREIGN KEY(post) REFERENCES posts(idx),FOREIGN KEY(tag) REFERENCES tags(tag))"
        )
        self.con.commit()

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS replies(
                post INTEGER,
                replying_to INTEGER,
                FOREIGN KEY(post) REFERENCES posts(idx),
                FOREIGN KEY(replying_to) REFERENCES posts(idx)
            );
            """)
        self.con.commit()

        # Ensure we can use a directory next to the DB for an object store
        db_dir = os.path.dirname(path)
        self.obj_dir = os.path.join(db_dir, "obj")
        try:
            os.makedirs(self.obj_dir)
        except:
            pass

    def name(self) -> str:
        return self._name

    def set_name(self, name: str):
        self._name = name

    async def put_obj(self, data: bytes) -> str | Exception:
        obj_id = core.random_id()
        obj_path = os.path.join(self.obj_dir, obj_id)
        with open(obj_path, "wb") as f:
            f.write(data)
        return obj_id

    async def get_obj(self, id: str) -> bytes | Exception:
        obj_path = os.path.join(self.obj_dir, id)
        with open(obj_path, "rb") as f:
            return f.read()

    # NOTE: Agents are expecting to index from zero, but SQLite starts with row idx 1
    async def read(self, idx: int) -> core.Post | Exception:
        adjusted_idx = idx + 1
        result = self.cur.execute(
            "SELECT idx,source,metadata,data FROM posts WHERE idx IS ?", (
                adjusted_idx,)
        )
        self.con.commit()

        post_data = result.fetchone()  # This should be unique
        if post_data is None:
            return RuntimeError(f"idx {adjusted_idx} not found")

        # Query the tags associated with the post
        result = self.cur.execute(
            "SELECT tag FROM post_tags WHERE post IS ?", (adjusted_idx,)
        )
        self.con.commit()

        tags = result.fetchall()  # This should be unique
        tag_list = [x[0] for x in tags]

        # Query replies
        result = self.cur.execute(
            "SELECT replying_to FROM replies WHERE post IS ?", (adjusted_idx,)
        )
        self.con.commit()

        replies = result.fetchall()  # This should be unique
        reply_list = [x[0] for x in replies]

        # argument for: agents should never really be dealing with those
        # indices directly. against: we expose the index to the user via the
        # post.index() method, if this
        # is not internally consistent, it will make for bad behavior.
        post = self.new_post()
        # this will return an index to the agent that they could use to 'read(idx)' to get the message back.
        post.set_index(post_data[0] - 1)
        post.set_source(post_data[1])
        post.set_tags(tag_list)
        post.set_metadata(post_data[2].encode())
        post.set_data(post_data[3].encode())
        post.set_replying_to(reply_list)

        # temporary kluge
        post._m_retrieved = False
        post._d_retrieved = False

        return post

    async def write(self, post: core.Post) -> None | Exception:
        # Indirect our data onto disk

        m_data = await post.metadata()
        if isinstance(m_data, Exception):
            return m_data

        metadata_obj_id = ""
        if len(m_data) > 0:
            metadata_obj_id = await self.put_obj(m_data)
            if isinstance(metadata_obj_id, Exception):
                return metadata_obj_id

        data = await post.data()
        if isinstance(data, Exception):
            return data

        data_obj_id = ""
        if len(data) > 0:
            data_obj_id = await self.put_obj(data)
            if isinstance(data_obj_id, Exception):
                return data_obj_id
            post.set_data(data_obj_id.encode())

        ins_post = (
            post.source(),
            metadata_obj_id,
            data_obj_id,
        )
        self.cur.execute(
            "INSERT INTO posts(source,metadata,data) VALUES(?,?,?)", ins_post
        )
        self.con.commit()

        post_idx = self.cur.lastrowid

        # Establish tags and links
        # Ensure the tags exist
        self.cur.executemany(
            "INSERT OR IGNORE INTO tags(tag) VALUES (?)",
            [(tag,) for tag in post.tags()],
        )
        self.con.commit()

        # Link the tags to the post
        tags = [(post_idx, tag) for tag in post.tags()]
        self.cur.executemany(
            "INSERT INTO post_tags(post, tag) VALUES(?,?)", tags)
        self.con.commit()

        # Establish any replying to

        replies = [(post_idx, replying_to)
                   for replying_to in post.replying_to()]
        self.cur.executemany(
            "INSERT INTO replies(post, replying_to) VALUES(?,?)", replies
        )
        self.con.commit()

        return None

    def new_post(self) -> core.Post:
        p = Post()
        p.bb = self
        p.set_source(self._name)
        return p

    async def len(self) -> int | Exception:
        res = self.cur.execute("SELECT COUNT(*) FROM posts")
        len_res = res.fetchone()
        return len_res[0]

import os
import psycopg2
from . import core
from .hardcore_post import Post


class PostgreSQLTransit(core.Blackboard):
    """
    PostgreSQLTransit is a proof of concept.  It can/will be matured
    if needed.  For now, it's only made available to illustrate
    the possible forward direction.
    """

    def __init__(self, path: str):
        self._name = "pg-tester"
        # self.con = psycopg2.connect("dbname=bb user=postgres")
        self.con = psycopg2.connect(path)

        self.cur = self.con.cursor()

        print(
            "WARN: PostgreSQLTransit is not a complete implementation and will only work in narrow use cases"
        )

        # provision the db if needed
        # "index" is "id" since index is a keyword
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS posts(
                idx BIGSERIAL PRIMARY KEY,
                source TEXT,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                data TEXT,
                encryption TEXT DEFAULT 'aes-gcm'
            );
            """)
        self.con.commit()

        self.cur.execute("CREATE TABLE IF NOT EXISTS tags(tag TEXT UNIQUE);")
        self.con.commit()

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS post_tags(
                post BIGINT REFERENCES posts(idx),
                tag TEXT REFERENCES tags(tag)
            );
            """)
        self.con.commit()

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS replies(
                post BIGINT REFERENCES posts(idx),
                replying_to BIGINT REFERENCES posts(idx)
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

    # NOTE: Agents are expecting to index from zero, but PostgreSQLite starts with row idx 1
    async def read(self, idx: int) -> core.Post | Exception:
        adjusted_idx = idx + 1
        self.cur.execute(
            "SELECT idx,source,metadata,data FROM posts WHERE idx = %s;",
            (adjusted_idx,),
        )
        self.con.commit()

        post_data = self.cur.fetchone()  # This should be unique
        if post_data is None:
            return RuntimeError(f"idx {adjusted_idx} not found")

        # Query the tags associated with the post
        self.cur.execute("SELECT tag FROM post_tags WHERE post = %s;", (adjusted_idx,))
        self.con.commit()

        tags = self.cur.fetchall()  # This should be unique
        tag_list = [x[0] for x in tags]

        # argument for: agents should never really be dealing with those indices directly
        # against: we expose the index to the user via the post.index() method, if this
        # is not internally consistent, it will make for bad behavior.
        post = self.new_post()
        # this will return an index to the agent that they could use to 'read(idx)' to get the message back.
        post.set_index(post_data[0] - 1)
        post.set_source(post_data[1])
        post.set_tags(tag_list)
        post.set_metadata(post_data[2].encode())
        post.set_data(post_data[3].encode())

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
            "INSERT INTO posts(source,metadata,data) VALUES(%s,%s,%s) RETURNING idx;",
            ins_post,
        )
        post_idx = self.cur.fetchone()
        self.con.commit()

        # Establish tags and links
        # Ensure the tags exist
        self.cur.executemany(
            "INSERT INTO tags(tag) VALUES (%s) ON CONFLICT DO NOTHING;",
            [(tag,) for tag in post.tags()],
        )
        self.con.commit()

        # Link the tags to the post
        tags = [(post_idx, tag) for tag in post.tags()]
        self.cur.executemany("INSERT INTO post_tags(post, tag) VALUES(%s,%s);", tags)
        self.con.commit()

        # Establish any replying to

        replies = [(post_idx, replying_to) for replying_to in post.replying_to()]
        self.cur.executemany(
            "INSERT INTO replies(post, replying_to) VALUES(%s,%s);", replies
        )
        self.con.commit()

        return None

    def new_post(self) -> core.Post:
        p = Post()
        p.bb = self
        p.set_source(self._name)
        return p

    async def len(self) -> int | Exception:
        self.cur.execute("SELECT COUNT(*) FROM posts;")
        len_res = self.cur.fetchone()
        return len_res[0]

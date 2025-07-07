import sqlite3


class PreciseDatasetLoaderV2:
    def __init__(self, db_path: str, lang: str):
        self.lang = {
            "js": "javascript",
            "py": "python",
            "sh": "bash"
        }[lang]
        self.lang_short = lang
        self.con = sqlite3.connect(db_path)

    def __del__(self):
        self.con.close()

    def __iter__(self):
        sql = """
        SELECT tarball_path, member_path, hash
        FROM mal
        WHERE lang = ? and review = 1
        GROUP BY hash
        """
        cur = self.con.cursor()
        res = cur.execute(sql, (self.lang_short,))
        while True:
            row = res.fetchone()
            if row is None:
                break
            tarball_path, member_path, hash_value = row
            content = self.load_codes(hash_value)
            if content is None:
                continue
            yield content, {"lang": self.lang_short, "tarball": tarball_path, "path": member_path, "hash": hash_value}

        # add package json
        if self.lang == "bash":
            sql = """
                    SELECT tarball_path, entry_point, hash
                    FROM package_json
                    WHERE review = 1
                    GROUP BY hash
                    """
            cur = self.con.cursor()
            res = cur.execute(sql)
            while True:
                row = res.fetchone()
                if row is None:
                    break
                tarball_path, entry_point, hash_value = row
                content = self.load_codes(hash_value, True)
                if content is None:
                    continue
                yield content, {"lang": self.lang_short, "tarball": tarball_path, "entry_point": entry_point,
                                "hash": hash_value}


    def iter_alert_cnt_1(self):
        if self.lang == "sh":
            return
        sql = """
                SELECT tarball_path, member_path, hash
                FROM mal
                WHERE lang = ? and alert_cnt >= 1 and review = -1
                GROUP BY hash
                """
        cur = self.con.cursor()
        res = cur.execute(sql, (self.lang_short,))
        while True:
            row = res.fetchone()
            if row is None:
                break
            tarball_path, member_path, hash_value = row
            content = self.load_codes(hash_value)
            if content is None:
                continue
            yield content, {"lang": self.lang_short, "tarball": tarball_path, "path": member_path, "hash": hash_value}

    def load_codes(self, hash_value, is_package_json=False):
        content_sql = f"""SELECT content FROM {'package_json_content' if is_package_json else 'content'} WHERE hash = ?"""
        content_cur = self.con.cursor()
        content_res = content_cur.execute(content_sql, (hash_value,))
        content_tuple = content_res.fetchone()
        if content_tuple is None:
            print("Error! No hash content")
            return None
        if is_package_json:
            return content_tuple[0].encode('utf-8')
        else:
            return content_tuple[0]



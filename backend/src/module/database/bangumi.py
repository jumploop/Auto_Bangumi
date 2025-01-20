import logging
from typing import Optional, List

from sqlalchemy.sql import func
from sqlmodel import Session, and_, delete, false, or_, select

from module.models import Bangumi, BangumiUpdate, Torrent

logger = logging.getLogger(__name__)


class BangumiDatabase:
    def __init__(self, session: Session):
        self.session = session

    def add(self, data: Bangumi) -> bool:
        if self.session.exec(select(Bangumi).where(Bangumi.title_raw == data.title_raw)).first():
            return False
        self.session.add(data)
        self.session.commit()
        logger.debug(f"[Database] Insert {data.official_title} into database.")
        return True

    def add_all(self, datas: list[Bangumi]) -> None:
        # 一次查询获取所有现有标题
        existing_titles = {
            result[0] for result in
            self.session.exec(select(Bangumi.title_raw)).all()
        }
        if new_records := [
            data for data in datas if data.title_raw not in existing_titles
        ]:
            self.session.add_all(new_records)
            self.session.commit()
            logger.debug(f"[数据库] 插入 {len(new_records)} 个番组到数据库。")

    def update(self, data: Bangumi | BangumiUpdate, _id: int = None) -> bool:
        if _id and isinstance(data, BangumiUpdate):
            db_data = self.session.get(Bangumi, _id)
        elif isinstance(data, Bangumi):
            db_data = self.session.get(Bangumi, data.id)
        else:
            return False
        if not db_data:
            return False
        for key, value in data.dict(exclude_unset=True).items():
            setattr(db_data, key, value)
        self.session.add(db_data)
        self.session.commit()
        self.session.refresh(db_data)
        logger.debug(f"[Database] Update {db_data.official_title}")
        return True

    def update_all(self, datas: list[Bangumi]) -> None:
        self.session.add_all(datas)
        self.session.commit()
        logger.debug(f"[Database] Update {len(datas)} bangumi.")

    def update_rss(self, title_raw, rss_set: str) -> None:
        # Update rss and added
        bangumi = self.session.exec(select(Bangumi).where(Bangumi.title_raw == title_raw)).first()
        if not bangumi:
            logger.warning(f"[Database] Update RSS 失败：未找到标题为 '{title_raw}' 的番组")
            return
        bangumi.rss_link = rss_set
        bangumi.added = False
        self.session.add(bangumi)
        self.session.commit()
        self.session.refresh(bangumi)
        logger.debug(f"[Database] Update {title_raw} rss_link to {rss_set}.")

    def update_poster(self, title_raw, poster_link: str) -> None:
        bangumi = self.session.exec(select(Bangumi).where(Bangumi.title_raw == title_raw)).first()
        if bangumi:
            bangumi.poster_link = poster_link
            self.session.add(bangumi)
            self.session.commit()
            self.session.refresh(bangumi)
            logger.debug(f"[Database] Update {title_raw} poster_link to {poster_link}.")

    def delete_one(self, _id: int) -> None:
        if bangumi := self.session.exec(select(Bangumi).where(Bangumi.id == _id)).first():
            self.session.delete(bangumi)
            self.session.commit()
            logger.debug(f"[Database] Delete bangumi id: {_id}.")

    def delete_all(self) -> None:
        self.session.exec(delete(Bangumi))
        self.session.commit()

    def search_all(self) -> list[Bangumi]:
        return self.session.exec(select(Bangumi)).all()

    def search_id(self, _id: int) -> Optional[Bangumi]:
        bangumi = self.session.exec(select(Bangumi).where(Bangumi.id == _id)).first()
        if bangumi:
            logger.debug(f"[Database] Find bangumi id: {_id}.")
            return bangumi
        else:
            logger.warning(f"[Database] Cannot find bangumi id: {_id}.")
            return None

    def match_poster(self, bangumi_name: str) -> str:
        # Use like to match
        if data := self.session.exec(
                select(Bangumi).where(func.instr(bangumi_name, Bangumi.official_title) > 0)).first():
            return data.poster_link
        return ""

    def match_list(self, torrent_list: List[Torrent], rss_link: str) -> List[Torrent]:
        match_datas = self.search_all()
        if not match_datas:
            return torrent_list
        i = 0
        while i < len(torrent_list):
            torrent = torrent_list[i]
            for match_data in match_datas:
                if match_data.title_raw in torrent.name:
                    if rss_link not in match_data.rss_link:
                        match_data.rss_link += f",{rss_link}"
                        self.update_rss(match_data.title_raw, match_data.rss_link)
                    torrent_list.pop(i)
                    break
            else:
                i += 1
        return torrent_list

    def match_torrent(self, torrent_name: str) -> Optional[Bangumi]:
        statement = select(Bangumi).where(
            and_(
                func.instr(torrent_name, Bangumi.title_raw) > 0,
                # use `false()` to avoid E712 checking
                # see: https://docs.astral.sh/ruff/rules/true-false-comparison/
                Bangumi.deleted == false(),
            )
        )
        return self.session.exec(statement).first()

    def not_complete(self) -> list[Bangumi]:
        # Find eps_complete = False
        # use `false()` to avoid E712 checking
        # see: https://docs.astral.sh/ruff/rules/true-false-comparison/
        condition = select(Bangumi).where(
            and_(Bangumi.eps_collect == false(), Bangumi.deleted == false())
        )
        return self.session.exec(condition).all()

    def not_added(self) -> list[Bangumi]:
        conditions = select(Bangumi).where(
            or_(
                Bangumi.added == 0, Bangumi.rule_name is None, Bangumi.save_path is None
            )
        )
        return self.session.exec(conditions).all()

    def disable_rule(self, _id: int):
        statement = select(Bangumi).where(Bangumi.id == _id)
        bangumi = self.session.exec(statement).first()
        bangumi.deleted = True
        self.session.add(bangumi)
        self.session.commit()
        self.session.refresh(bangumi)
        logger.debug(f"[Database] Disable rule {bangumi.title_raw}.")

    def search_rss(self, rss_link: str) -> list[Bangumi]:
        statement = select(Bangumi).where(func.instr(rss_link, Bangumi.rss_link) > 0)
        return self.session.exec(statement).all()

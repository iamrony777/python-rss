from fastapi.routing import APIRouter
from fastapi.responses import Response
from asyncio import run
from ..modules.reddit import Reddit

router = APIRouter(prefix="/r")


@router.get("/{subreddit}")
def return_subreddit_feed(subreddit: str):
    return Response(
        content=run(Reddit().get_feed(subreddit=subreddit)),
        media_type="application/xml; charset=utf-8",
    )

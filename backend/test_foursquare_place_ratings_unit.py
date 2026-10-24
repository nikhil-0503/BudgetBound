import asyncio
import unittest
from unittest.mock import AsyncMock, patch
import httpx
from app.services import foursquare_place_ratings as ratings


def candidate(name="Ooty", lat=11.41, lon=76.69):
    return {"name":name,"latitude":lat,"longitude":lon,"region":"Tamil Nadu","country":"India"}


def place(**changes):
    row={"fsq_place_id":"fsq-1","name":"Ooty","latitude":11.41,"longitude":76.69,"rating":8.4,"stats":{"total_ratings":132},"link":"https://foursquare.com/place/fsq-1"}
    row.update(changes); return row


class FoursquareRatingsTests(unittest.TestCase):
    def setUp(self): ratings.clear_rating_cache()

    def test_normalizes_rating_and_missing_count_only_from_provider_fields(self):
        result=ratings.normalize_match(candidate(),place())
        self.assertEqual((result["rating"],result["rating_scale"],result["review_count"]),(8.4,10,132))
        self.assertIsNone(ratings.normalize_match(candidate(),place(stats={}))["review_count"])
        self.assertIsNone(ratings.normalize_match(candidate(),place().copy() | {"rating":None})["rating"])

    def test_rejects_distant_and_unrelated_candidates(self):
        self.assertIsNone(ratings.normalize_match(candidate(),place(latitude=40,longitude=-70)))
        self.assertIsNone(ratings.normalize_match(candidate(),place(name="Completely Different")))

    def test_uses_documented_endpoint_auth_version_and_cache(self):
        async def run():
            response=httpx.Response(200,json={"results":[place()]},request=httpx.Request("GET",ratings.SEARCH_URL))
            with patch.object(ratings.settings,"FOURSQUARE_API_KEY","unit-test-key"), patch("app.services.foursquare_place_ratings.httpx.AsyncClient") as client_type:
                client_type.return_value.__aenter__.return_value.get=AsyncMock(return_value=response)
                first=await ratings.search_candidate(candidate()); second=await ratings.search_candidate(candidate())
                args,kwargs=client_type.return_value.__aenter__.return_value.get.await_args
                self.assertEqual(args[0],ratings.SEARCH_URL)
                self.assertEqual(kwargs["headers"]["Authorization"],"Bearer unit-test-key")
                self.assertEqual(kwargs["headers"]["X-Places-Api-Version"],"2025-06-17")
                self.assertEqual(first["rating"],second["rating"])
                self.assertEqual(client_type.return_value.__aenter__.return_value.get.await_count,1)
        asyncio.run(run())

    def test_quota_and_invalid_credentials_are_structured(self):
        async def run(status, expected):
            response=httpx.Response(status,request=httpx.Request("GET",ratings.SEARCH_URL))
            with patch.object(ratings.settings,"FOURSQUARE_API_KEY","key"), patch("app.services.foursquare_place_ratings.httpx.AsyncClient") as client_type:
                client_type.return_value.__aenter__.return_value.get=AsyncMock(return_value=response)
                with self.assertRaises(ratings.FoursquareRatingError) as err: await ratings.search_candidate(candidate())
                self.assertEqual(err.exception.diagnostic_code,expected)
        asyncio.run(run(429,"quota_exceeded")); asyncio.run(run(401,"invalid_credentials"))

    def test_missing_key_keeps_candidate_with_unavailable_state(self):
        async def run():
            rows=[candidate()]
            with patch.object(ratings.settings,"FOURSQUARE_API_KEY",""):
                await ratings.enrich_candidates(rows)
            self.assertEqual(rows[0]["status"],"missing_credentials")
            self.assertIsNone(rows[0]["rating"])
        asyncio.run(run())


if __name__ == "__main__": unittest.main()

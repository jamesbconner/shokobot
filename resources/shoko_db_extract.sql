/* The Shoko default DB is a SQLite file called JMMServer.db3 */
SELECT
  ada.AniDB_AnimeID,
  ada.AnimeID,
  ada.EpisodeCountNormal,
  ada.EpisodeCountSpecial,
  ada.BeginYear,
  ada.EndYear,ada.AirDate,
  ada.MainTitle,
  ada.AllTitles,
  ada.AllTags,
  ada.Description,
  ada.Rating,
  ada.VoteCount,
  ada.AvgReviewRating,
  ada.ReviewCount,
  ada.ANNID,
  ada.CrunchyrollID,
  /* relations: [{anime_id, relation_type, title_main, begin_year, end_year}] */
  (
    SELECT json_group_array(
             json_object(
               'anime_id',    r.RelatedAnimeID,
               'relation_type', r.RelationType,
               'title_main',  a2.MainTitle,
               'begin_year',  a2.BeginYear,
               'end_year',    a2.EndYear
             )
           )
    FROM (
      SELECT DISTINCT r.RelatedAnimeID, r.RelationType
      FROM AniDB_Anime_Relation r
      WHERE r.AnimeID = ada.AnimeID
    ) AS r
    JOIN AniDB_Anime a2
      ON a2.AnimeID = r.RelatedAnimeID
    /* stable output order is optional, use a subselect if ordering needed */
  ) AS relations,

  /* similar: [{anime_id, approval_agree, approval_total, title_main, begin_year, end_year}] */
  (
    SELECT json_group_array(
             json_object(
               'anime_id',        s.SimilarAnimeID,
               'approval_agree',  COALESCE(s.Approval, 0),
               'approval_total',  COALESCE(s.Total, 0),
               'title_main',      a3.MainTitle,
               'begin_year',      a3.BeginYear,
               'end_year',        a3.EndYear
             )
           )
    FROM (
      SELECT DISTINCT s.SimilarAnimeID, s.Approval, s.Total
      FROM AniDB_Anime_Similar s
      WHERE s.AnimeID = ada.AnimeID
    ) AS s
    JOIN AniDB_Anime a3
      ON a3.AnimeID = s.SimilarAnimeID
  ) AS similar

FROM AniDB_Anime AS ada
WHERE ada.Restricted <> 1;
--
-- PostgreSQL database dump
--

-- Dumped from database version 16.3 (Debian 16.3-1.pgdg120+1)
-- Dumped by pg_dump version 16.3 (Debian 16.3-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: openalex; Type: SCHEMA; Schema: -; Owner: AithenaAdmin
--

CREATE SCHEMA openalex;


ALTER SCHEMA openalex OWNER TO "AithenaAdmin";

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: authors; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.authors (
    id text NOT NULL,
    orcid text,
    display_name text,
    display_name_alternatives json,
    works_count integer,
    cited_by_count integer,
    last_known_institution text,
    works_api_url text,
    updated_date timestamp without time zone
);


ALTER TABLE openalex.authors OWNER TO "AithenaAdmin";

--
-- Name: authors_counts_by_year; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.authors_counts_by_year (
    author_id text NOT NULL,
    year integer NOT NULL,
    works_count integer,
    cited_by_count integer,
    oa_works_count integer
);


ALTER TABLE openalex.authors_counts_by_year OWNER TO "AithenaAdmin";

--
-- Name: authors_ids; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.authors_ids (
    author_id text NOT NULL,
    openalex text,
    orcid text,
    scopus text,
    twitter text,
    wikipedia text,
    mag bigint
);


ALTER TABLE openalex.authors_ids OWNER TO "AithenaAdmin";

--
-- Name: concepts; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.concepts (
    id text NOT NULL,
    wikidata text,
    display_name text,
    level integer,
    description text,
    works_count integer,
    cited_by_count integer,
    image_url text,
    image_thumbnail_url text,
    works_api_url text,
    updated_date timestamp without time zone
);


ALTER TABLE openalex.concepts OWNER TO "AithenaAdmin";

--
-- Name: concepts_ancestors; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.concepts_ancestors (
    concept_id text,
    ancestor_id text
);


ALTER TABLE openalex.concepts_ancestors OWNER TO "AithenaAdmin";

--
-- Name: concepts_counts_by_year; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.concepts_counts_by_year (
    concept_id text NOT NULL,
    year integer NOT NULL,
    works_count integer,
    cited_by_count integer,
    oa_works_count integer
);


ALTER TABLE openalex.concepts_counts_by_year OWNER TO "AithenaAdmin";

--
-- Name: concepts_ids; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.concepts_ids (
    concept_id text NOT NULL,
    openalex text,
    wikidata text,
    wikipedia text,
    umls_aui json,
    umls_cui json,
    mag bigint
);


ALTER TABLE openalex.concepts_ids OWNER TO "AithenaAdmin";

--
-- Name: concepts_related_concepts; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.concepts_related_concepts (
    concept_id text,
    related_concept_id text,
    score real
);


ALTER TABLE openalex.concepts_related_concepts OWNER TO "AithenaAdmin";

--
-- Name: embeddings_nomic_embed_text_768; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.embeddings_nomic_embed_text_768 (
    embedding public.vector(768),
    work_id text NOT NULL
);


ALTER TABLE openalex.embeddings_nomic_embed_text_768 OWNER TO "AithenaAdmin";

--
-- Name: index_works; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.index_works (
    row_number bigint,
    id text
);


ALTER TABLE openalex.index_works OWNER TO "AithenaAdmin";

--
-- Name: institutions; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.institutions (
    id text NOT NULL,
    ror text,
    display_name text,
    country_code text,
    type text,
    homepage_url text,
    image_url text,
    image_thumbnail_url text,
    display_name_acronyms json,
    display_name_alternatives json,
    works_count integer,
    cited_by_count integer,
    works_api_url text,
    updated_date timestamp without time zone
);


ALTER TABLE openalex.institutions OWNER TO "AithenaAdmin";

--
-- Name: institutions_associated_institutions; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.institutions_associated_institutions (
    institution_id text,
    associated_institution_id text,
    relationship text
);


ALTER TABLE openalex.institutions_associated_institutions OWNER TO "AithenaAdmin";

--
-- Name: institutions_counts_by_year; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.institutions_counts_by_year (
    institution_id text NOT NULL,
    year integer NOT NULL,
    works_count integer,
    cited_by_count integer,
    oa_works_count integer
);


ALTER TABLE openalex.institutions_counts_by_year OWNER TO "AithenaAdmin";

--
-- Name: institutions_geo; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.institutions_geo (
    institution_id text NOT NULL,
    city text,
    geonames_city_id text,
    region text,
    country_code text,
    country text,
    latitude real,
    longitude real
);


ALTER TABLE openalex.institutions_geo OWNER TO "AithenaAdmin";

--
-- Name: institutions_ids; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.institutions_ids (
    institution_id text NOT NULL,
    openalex text,
    ror text,
    grid text,
    wikipedia text,
    wikidata text,
    mag bigint
);


ALTER TABLE openalex.institutions_ids OWNER TO "AithenaAdmin";

--
-- Name: new_embeddings_nomic_embed_text_768; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.new_embeddings_nomic_embed_text_768 (
    embedding public.vector(768),
    work_id text NOT NULL
);


ALTER TABLE openalex.new_embeddings_nomic_embed_text_768 OWNER TO "AithenaAdmin";

--
-- Name: new_nomic_embed_text_768; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.new_nomic_embed_text_768 (
    embedding public.vector(768),
    work_id text NOT NULL
);


ALTER TABLE openalex.new_nomic_embed_text_768 OWNER TO "AithenaAdmin";

--
-- Name: nomic_embed_text_768; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.nomic_embed_text_768 (
    embedding public.vector(768),
    work_id text NOT NULL
);


ALTER TABLE openalex.nomic_embed_text_768 OWNER TO "AithenaAdmin";

--
-- Name: nomic_embed_text_768_no_prefix; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.nomic_embed_text_768_no_prefix (
    embedding public.vector(768),
    work_id text NOT NULL
);


ALTER TABLE openalex.nomic_embed_text_768_no_prefix OWNER TO "AithenaAdmin";

--
-- Name: publishers; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.publishers (
    id text NOT NULL,
    display_name text,
    alternate_titles json,
    country_codes json,
    hierarchy_level integer,
    parent_publisher text,
    works_count integer,
    cited_by_count integer,
    sources_api_url text,
    updated_date timestamp without time zone
);


ALTER TABLE openalex.publishers OWNER TO "AithenaAdmin";

--
-- Name: publishers_counts_by_year; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.publishers_counts_by_year (
    publisher_id text NOT NULL,
    year integer NOT NULL,
    works_count integer,
    cited_by_count integer,
    oa_works_count integer
);


ALTER TABLE openalex.publishers_counts_by_year OWNER TO "AithenaAdmin";

--
-- Name: publishers_ids; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.publishers_ids (
    publisher_id text,
    openalex text,
    ror text,
    wikidata text
);


ALTER TABLE openalex.publishers_ids OWNER TO "AithenaAdmin";

--
-- Name: sources; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.sources (
    id text NOT NULL,
    issn_l text,
    issn json,
    display_name text,
    publisher text,
    works_count integer,
    cited_by_count integer,
    is_oa boolean,
    is_in_doaj boolean,
    homepage_url text,
    works_api_url text,
    updated_date timestamp without time zone
);


ALTER TABLE openalex.sources OWNER TO "AithenaAdmin";

--
-- Name: sources_counts_by_year; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.sources_counts_by_year (
    source_id text NOT NULL,
    year integer NOT NULL,
    works_count integer,
    cited_by_count integer,
    oa_works_count integer
);


ALTER TABLE openalex.sources_counts_by_year OWNER TO "AithenaAdmin";

--
-- Name: sources_ids; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.sources_ids (
    source_id text,
    openalex text,
    issn_l text,
    issn json,
    mag bigint,
    wikidata text,
    fatcat text
);


ALTER TABLE openalex.sources_ids OWNER TO "AithenaAdmin";

--
-- Name: test_embeddings_nomic_embed_text_768; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.test_embeddings_nomic_embed_text_768 (
    embedding public.vector(768),
    work_id text
);


ALTER TABLE openalex.test_embeddings_nomic_embed_text_768 OWNER TO "AithenaAdmin";

--
-- Name: topics; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.topics (
    id text NOT NULL,
    display_name text,
    subfield_id text,
    subfield_display_name text,
    field_id text,
    field_display_name text,
    domain_id text,
    domain_display_name text,
    description text,
    keywords text,
    works_api_url text,
    wikipedia_id text,
    works_count integer,
    cited_by_count integer,
    updated_date timestamp without time zone
);


ALTER TABLE openalex.topics OWNER TO "AithenaAdmin";

--
-- Name: works; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.works (
    id text NOT NULL,
    doi text,
    title text,
    display_name text,
    publication_year integer,
    publication_date text,
    type text,
    cited_by_count integer,
    is_retracted boolean,
    is_paratext boolean,
    cited_by_api_url text,
    abstract_inverted_index json,
    language text
);


ALTER TABLE openalex.works OWNER TO "AithenaAdmin";

--
-- Name: works_authorships; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.works_authorships (
    work_id text,
    author_position text,
    author_id text,
    institution_id text,
    raw_affiliation_string text
);


ALTER TABLE openalex.works_authorships OWNER TO "AithenaAdmin";

--
-- Name: works_best_oa_locations; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.works_best_oa_locations (
    work_id text,
    source_id text,
    landing_page_url text,
    pdf_url text,
    is_oa boolean,
    version text,
    license text
);


ALTER TABLE openalex.works_best_oa_locations OWNER TO "AithenaAdmin";

--
-- Name: works_biblio; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.works_biblio (
    work_id text NOT NULL,
    volume text,
    issue text,
    first_page text,
    last_page text
);


ALTER TABLE openalex.works_biblio OWNER TO "AithenaAdmin";

--
-- Name: works_concepts; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.works_concepts (
    work_id text,
    concept_id text,
    score real
);


ALTER TABLE openalex.works_concepts OWNER TO "AithenaAdmin";

--
-- Name: works_ids; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.works_ids (
    work_id text NOT NULL,
    openalex text,
    doi text,
    mag bigint,
    pmid text,
    pmcid text
);


ALTER TABLE openalex.works_ids OWNER TO "AithenaAdmin";

--
-- Name: works_locations; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.works_locations (
    work_id text,
    source_id text,
    landing_page_url text,
    pdf_url text,
    is_oa boolean,
    version text,
    license text
);


ALTER TABLE openalex.works_locations OWNER TO "AithenaAdmin";

--
-- Name: works_mesh; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.works_mesh (
    work_id text,
    descriptor_ui text,
    descriptor_name text,
    qualifier_ui text,
    qualifier_name text,
    is_major_topic boolean
);


ALTER TABLE openalex.works_mesh OWNER TO "AithenaAdmin";

--
-- Name: works_open_access; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.works_open_access (
    work_id text NOT NULL,
    is_oa boolean,
    oa_status text,
    oa_url text,
    any_repository_has_fulltext boolean
);


ALTER TABLE openalex.works_open_access OWNER TO "AithenaAdmin";

--
-- Name: works_primary_locations; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.works_primary_locations (
    work_id text,
    source_id text,
    landing_page_url text,
    pdf_url text,
    is_oa boolean,
    version text,
    license text
);


ALTER TABLE openalex.works_primary_locations OWNER TO "AithenaAdmin";

--
-- Name: works_referenced_works; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.works_referenced_works (
    work_id text,
    referenced_work_id text
);


ALTER TABLE openalex.works_referenced_works OWNER TO "AithenaAdmin";

--
-- Name: works_related_works; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.works_related_works (
    work_id text,
    related_work_id text
);


ALTER TABLE openalex.works_related_works OWNER TO "AithenaAdmin";

--
-- Name: works_topics; Type: TABLE; Schema: openalex; Owner: AithenaAdmin
--

CREATE TABLE openalex.works_topics (
    work_id text,
    topic_id text,
    score real
);


ALTER TABLE openalex.works_topics OWNER TO "AithenaAdmin";

--
-- Name: embeddings_nomic_embed_text_768 embeddings_nomic_embed_text_768_pkey; Type: CONSTRAINT; Schema: openalex; Owner: AithenaAdmin
--

ALTER TABLE ONLY openalex.embeddings_nomic_embed_text_768
    ADD CONSTRAINT embeddings_nomic_embed_text_768_pkey PRIMARY KEY (work_id);


--
-- Name: new_embeddings_nomic_embed_text_768 new_embeddings_nomic_embed_text_768_pkey; Type: CONSTRAINT; Schema: openalex; Owner: AithenaAdmin
--

ALTER TABLE ONLY openalex.new_embeddings_nomic_embed_text_768
    ADD CONSTRAINT new_embeddings_nomic_embed_text_768_pkey PRIMARY KEY (work_id);


--
-- Name: new_nomic_embed_text_768 new_nomic_embed_text_768_pkey; Type: CONSTRAINT; Schema: openalex; Owner: AithenaAdmin
--

ALTER TABLE ONLY openalex.new_nomic_embed_text_768
    ADD CONSTRAINT new_nomic_embed_text_768_pkey PRIMARY KEY (work_id);


--
-- Name: nomic_embed_text_768_no_prefix nomic_embed_text_768_pkey; Type: CONSTRAINT; Schema: openalex; Owner: AithenaAdmin
--

ALTER TABLE ONLY openalex.nomic_embed_text_768_no_prefix
    ADD CONSTRAINT nomic_embed_text_768_pkey PRIMARY KEY (work_id);


--
-- Name: nomic_embed_text_768 nomic_embed_text_768_pkey1; Type: CONSTRAINT; Schema: openalex; Owner: AithenaAdmin
--

ALTER TABLE ONLY openalex.nomic_embed_text_768
    ADD CONSTRAINT nomic_embed_text_768_pkey1 PRIMARY KEY (work_id);


--
-- Name: works openalex_works_pkey; Type: CONSTRAINT; Schema: openalex; Owner: AithenaAdmin
--

ALTER TABLE ONLY openalex.works
    ADD CONSTRAINT openalex_works_pkey PRIMARY KEY (id);


--
-- Name: concepts_ancestors_concept_id_idx; Type: INDEX; Schema: openalex; Owner: AithenaAdmin
--

CREATE INDEX concepts_ancestors_concept_id_idx ON openalex.concepts_ancestors USING btree (concept_id);


--
-- Name: concepts_related_concepts_concept_id_idx; Type: INDEX; Schema: openalex; Owner: AithenaAdmin
--

CREATE INDEX concepts_related_concepts_concept_id_idx ON openalex.concepts_related_concepts USING btree (concept_id);


--
-- Name: concepts_related_concepts_related_concept_id_idx; Type: INDEX; Schema: openalex; Owner: AithenaAdmin
--

CREATE INDEX concepts_related_concepts_related_concept_id_idx ON openalex.concepts_related_concepts USING btree (related_concept_id);


--
-- Name: idx_index_works_row_number; Type: INDEX; Schema: openalex; Owner: AithenaAdmin
--

CREATE INDEX idx_index_works_row_number ON openalex.index_works USING btree (row_number);


--
-- Name: index_institutions_id; Type: INDEX; Schema: openalex; Owner: AithenaAdmin
--

CREATE INDEX index_institutions_id ON openalex.institutions USING btree (id) WITH (deduplicate_items='true');


--
-- Name: index_nomic_embed_text_768_embedding; Type: INDEX; Schema: openalex; Owner: AithenaAdmin
--

CREATE INDEX index_nomic_embed_text_768_embedding ON openalex.nomic_embed_text_768 USING hnsw (embedding public.vector_cosine_ops) WITH (m='48', ef_construction='100');


--
-- Name: index_works_authorships_author_id; Type: INDEX; Schema: openalex; Owner: AithenaAdmin
--

CREATE INDEX index_works_authorships_author_id ON openalex.works_authorships USING btree (author_id);


--
-- Name: index_works_authorships_work_id; Type: INDEX; Schema: openalex; Owner: AithenaAdmin
--

CREATE INDEX index_works_authorships_work_id ON openalex.works_authorships USING btree (work_id) WITH (deduplicate_items='true');


--
-- Name: test_embeddings_nomic_embed_text_768_embedding_idx; Type: INDEX; Schema: openalex; Owner: AithenaAdmin
--

CREATE INDEX test_embeddings_nomic_embed_text_768_embedding_idx ON openalex.test_embeddings_nomic_embed_text_768 USING hnsw (embedding public.vector_cosine_ops);


--
-- Name: works_best_oa_locations_work_id_idx; Type: INDEX; Schema: openalex; Owner: AithenaAdmin
--

CREATE INDEX works_best_oa_locations_work_id_idx ON openalex.works_best_oa_locations USING btree (work_id);


--
-- Name: works_locations_work_id_idx; Type: INDEX; Schema: openalex; Owner: AithenaAdmin
--

CREATE INDEX works_locations_work_id_idx ON openalex.works_locations USING btree (work_id);


--
-- Name: works_primary_locations_work_id_idx; Type: INDEX; Schema: openalex; Owner: AithenaAdmin
--

CREATE INDEX works_primary_locations_work_id_idx ON openalex.works_primary_locations USING btree (work_id);


--
-- Name: embeddings_nomic_embed_text_768 embeddings_nomic_embed_text_768_work_id_fkey; Type: FK CONSTRAINT; Schema: openalex; Owner: AithenaAdmin
--

ALTER TABLE ONLY openalex.embeddings_nomic_embed_text_768
    ADD CONSTRAINT embeddings_nomic_embed_text_768_work_id_fkey FOREIGN KEY (work_id) REFERENCES openalex.works(id);


--
-- Name: new_embeddings_nomic_embed_text_768 new_embeddings_nomic_embed_text_768_work_id_fkey; Type: FK CONSTRAINT; Schema: openalex; Owner: AithenaAdmin
--

ALTER TABLE ONLY openalex.new_embeddings_nomic_embed_text_768
    ADD CONSTRAINT new_embeddings_nomic_embed_text_768_work_id_fkey FOREIGN KEY (work_id) REFERENCES openalex.works(id);


--
-- Name: new_nomic_embed_text_768 new_nomic_embed_text_768_work_id_fkey; Type: FK CONSTRAINT; Schema: openalex; Owner: AithenaAdmin
--

ALTER TABLE ONLY openalex.new_nomic_embed_text_768
    ADD CONSTRAINT new_nomic_embed_text_768_work_id_fkey FOREIGN KEY (work_id) REFERENCES openalex.works(id);


--
-- Name: nomic_embed_text_768_no_prefix nomic_embed_text_768_work_id_fkey; Type: FK CONSTRAINT; Schema: openalex; Owner: AithenaAdmin
--

ALTER TABLE ONLY openalex.nomic_embed_text_768_no_prefix
    ADD CONSTRAINT nomic_embed_text_768_work_id_fkey FOREIGN KEY (work_id) REFERENCES openalex.works(id);


--
-- Name: nomic_embed_text_768 nomic_embed_text_768_work_id_fkey1; Type: FK CONSTRAINT; Schema: openalex; Owner: AithenaAdmin
--

ALTER TABLE ONLY openalex.nomic_embed_text_768
    ADD CONSTRAINT nomic_embed_text_768_work_id_fkey1 FOREIGN KEY (work_id) REFERENCES openalex.works(id);


--
-- Name: SCHEMA openalex; Type: ACL; Schema: -; Owner: AithenaAdmin
--

GRANT USAGE ON SCHEMA openalex TO oa_read;


--
-- Name: TABLE authors; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.authors TO oa_read;


--
-- Name: TABLE authors_counts_by_year; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.authors_counts_by_year TO oa_read;


--
-- Name: TABLE authors_ids; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.authors_ids TO oa_read;


--
-- Name: TABLE concepts; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.concepts TO oa_read;


--
-- Name: TABLE concepts_ancestors; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.concepts_ancestors TO oa_read;


--
-- Name: TABLE concepts_counts_by_year; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.concepts_counts_by_year TO oa_read;


--
-- Name: TABLE concepts_ids; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.concepts_ids TO oa_read;


--
-- Name: TABLE concepts_related_concepts; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.concepts_related_concepts TO oa_read;


--
-- Name: TABLE embeddings_nomic_embed_text_768; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.embeddings_nomic_embed_text_768 TO oa_read;


--
-- Name: TABLE index_works; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.index_works TO oa_read;


--
-- Name: TABLE institutions; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.institutions TO oa_read;


--
-- Name: TABLE institutions_associated_institutions; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.institutions_associated_institutions TO oa_read;


--
-- Name: TABLE institutions_counts_by_year; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.institutions_counts_by_year TO oa_read;


--
-- Name: TABLE institutions_geo; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.institutions_geo TO oa_read;


--
-- Name: TABLE institutions_ids; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.institutions_ids TO oa_read;


--
-- Name: TABLE new_embeddings_nomic_embed_text_768; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.new_embeddings_nomic_embed_text_768 TO oa_read;


--
-- Name: TABLE new_nomic_embed_text_768; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.new_nomic_embed_text_768 TO oa_read;


--
-- Name: TABLE nomic_embed_text_768; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.nomic_embed_text_768 TO oa_read;


--
-- Name: TABLE nomic_embed_text_768_no_prefix; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.nomic_embed_text_768_no_prefix TO oa_read;


--
-- Name: TABLE publishers; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.publishers TO oa_read;


--
-- Name: TABLE publishers_counts_by_year; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.publishers_counts_by_year TO oa_read;


--
-- Name: TABLE publishers_ids; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.publishers_ids TO oa_read;


--
-- Name: TABLE sources; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.sources TO oa_read;


--
-- Name: TABLE sources_counts_by_year; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.sources_counts_by_year TO oa_read;


--
-- Name: TABLE sources_ids; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.sources_ids TO oa_read;


--
-- Name: TABLE test_embeddings_nomic_embed_text_768; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.test_embeddings_nomic_embed_text_768 TO oa_read;


--
-- Name: TABLE topics; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.topics TO oa_read;


--
-- Name: TABLE works; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.works TO oa_read;


--
-- Name: TABLE works_authorships; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.works_authorships TO oa_read;


--
-- Name: TABLE works_best_oa_locations; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.works_best_oa_locations TO oa_read;


--
-- Name: TABLE works_biblio; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.works_biblio TO oa_read;


--
-- Name: TABLE works_concepts; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.works_concepts TO oa_read;


--
-- Name: TABLE works_ids; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.works_ids TO oa_read;


--
-- Name: TABLE works_locations; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.works_locations TO oa_read;


--
-- Name: TABLE works_mesh; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.works_mesh TO oa_read;


--
-- Name: TABLE works_open_access; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.works_open_access TO oa_read;


--
-- Name: TABLE works_primary_locations; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.works_primary_locations TO oa_read;


--
-- Name: TABLE works_referenced_works; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.works_referenced_works TO oa_read;


--
-- Name: TABLE works_related_works; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.works_related_works TO oa_read;


--
-- Name: TABLE works_topics; Type: ACL; Schema: openalex; Owner: AithenaAdmin
--

GRANT SELECT ON TABLE openalex.works_topics TO oa_read;


--
-- PostgreSQL database dump complete
--


-- CREATE INDEX idx_work ON my_table(text_column);

ALTER TABLE openalex.works
ADD CONSTRAINT openalex_works_pkey PRIMARY KEY (id);
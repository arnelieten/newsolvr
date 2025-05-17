CREATE TABLE public.problems (
    uid bigserial NOT NULL,
    title_article text NULL,
    description_article text NULL,
    content_article text NULL,
    link_article text NULL UNIQUE,
    published_date date
);
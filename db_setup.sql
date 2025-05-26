CREATE TABLE public.newsolvr (
    uid bigserial PRIMARY KEY,
    title_article text NULL,
    description_article text NULL,
    content_article text NULL,
    link_article text NULL UNIQUE,
    published_date date,
    problem_verified text NULL,
    problem_summary text NULL, 
    target_market text NULL, 
    startup_idea text NULL, 
    business_model text NULL
);
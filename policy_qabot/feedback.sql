-- use langchain_policy_bot;
-- -- -- drop table langchain_policy_bot.feedback;
-- ALTER TABLE langchain_policy_bot.response_table SET TBLPROPERTIES('delta.feature.allowColumnDefaults' = 'supported');
CREATE OR REPLACE TABLE langchain_policy_bot.response_table (
    response_id LONG GENERATED ALWAYS AS IDENTITY,
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    model STRING,
    response_type STRING,
    response_score STRING,
    response_text STRING,
    user_id STRING,
    metadata STRING,
    question STRING,
    answer STRING
);
-- -- ALTER TABLE response_feedbacks SET TBLPROPERTIES('delta.feature.allowColumnDefaults' = 'supported');
select * from langchain_policy_bot.response_table;

%sql
CREATE OR REPLACE TABLE qa_metrics (
    feedback_id BIGINT,
    model_endpoint STRING NOT NULL,
    request_id BIGINT NOT NULL,
    question STRING NOT NULL,
    answer STRING NOT NULL,
    response_ms INT,
    tokens_used INT,
    comment STRING,
    rating INT,
    created_on TIMESTAMP
    );

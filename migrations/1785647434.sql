CREATE TABLE IF NOT EXISTS BannedEmoji(
	id 		 	SERIAL PRIMARY KEY,
    emoji_id 	BIGINT,
    guild_id 	BIGINT,
	channel_id	BIGINT,
	reason 	 	TEXT DEFAULT 'That emoji was banned.',
	CONSTRAINT UC_Person UNIQUE (guild_id,emoji_id)
);

CREATE INDEX IF NOT EXISTS banned_emoji_guild_idx ON BannedEmoji(guild_id)
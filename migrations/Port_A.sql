-- Date: 7/27/26
-- Move from legacy SKU to making our main object of engagement the primary key

CREATE TABLE IF NOT EXISTS Starboards (
	guild_id BIGINT PRIMARY KEY,
	channel_id BIGINT,
	post_requirement INT CHECK(post_requirement > 0) DEFAULT 5,
	locked		BOOLEAN DEFAULT FALSE,
	created_on TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS StarEntry (
	message_id BIGINT PRIMARY KEY,
	guild_id BIGINT NOT NULL,
	author_id BIGINT NOT NULL,
	bot_message_id BIGINT,
	total_stars INT CHECK(total_stars>=0),
	created_on TIMESTAMP DEFAULT current_timestamp,

	CONSTRAINT fk_entry_stars
/**/			FOREIGN KEY (guild_id)
/**/			REFERENCES Starboards(guild_id)
/**/			ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Starer (
	user_id	BIGINT,
	message_id BIGINT NOT NULL,
	guild_id BIGINT NOT NULL,

	PRIMARY KEY(user_id, message_id),
	
	CONSTRAINT fk_starer_entry
/**/			FOREIGN KEY (message_id)
/**/			REFERENCES StarEntry(message_id)
/**/			ON DELETE CASCADE

);

CREATE INDEX IF NOT EXISTS star_idx ON StarEntry(author_id);

CREATE TABLE IF NOT EXISTS
	GuildHackban (
		GuildId BIGINT NOT NULL,
		UserId BIGINT NOT NULL,
		BannedOn TIMESTAMP DEFAULT NOW()
	);

CREATE INDEX IF NOT EXISTS idx_guild_hackban_pair ON GuildHackban (GuildId, UserId);

CREATE TABLE IF NOT EXISTS GuildDefaultRole (
	GuildId BIGINT NOT NULL,
	RoleId BIGINT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_default_role_pair ON GuildDefaultRole (GuildId, RoleId);

-- == Old -> V1 ==
--DROP TABLE defaultrole;
--DROP TABLE gemcontributor;
--DROP TABLE gementry;
--DROP TABLE gems;
--DROP TABLE guildhackban;
-- == Old -> V1 ==

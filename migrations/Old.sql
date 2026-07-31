-- Date: 7/27/26
-- Reason: Re-import of the old java schema

CREATE TABLE IF NOT EXISTS
	Gems (
		SKU UUID DEFAULT gen_random_uuid () PRIMARY KEY,
		GuildId BIGINT NOT NULL,
		ChannelId BIGINT NOT NULL,
		Locked BOOLEAN DEFAULT FALSE,
		TrackPrevious BOOLEAN DEFAULT TRUE, -- Explanation: If there were gems put on a message
		-- prior to this feature being added, we may want to 
		-- allow those to be added as well. This field allows
		-- our server owner to turn it off.
		Threshold INT DEFAULT 2,
		CreatedOn TIMESTAMP DEFAULT NOW()
	);

CREATE TABLE IF NOT EXISTS
	GemEntry (
		SKU UUID DEFAULT gen_random_uuid () PRIMARY KEY,
		GuildId BIGINT NOT NULL,
		MessageId BIGINT NOT NULL, -- This is the message id itself
		MessageAuthorId BIGINT NOT NULL, -- This is the the author of the original messages user id
		BotMessageId BIGINT NOT NULL, -- This is what the bot posted in the gem channel
		Tally BIGINT NOT NULL,
		CreatedOn TIMESTAMP DEFAULT NOW()
	);

CREATE TABLE IF NOT EXISTS
	GemContributor (
		SKU UUID DEFAULT gen_random_uuid () PRIMARY KEY,
		UserId BIGINT NOT NULL,
		MessageID BIGINT NOT NULL,
		CreatedOn TIMESTAMP DEFAULT NOW()
	);

CREATE INDEX IF NOT EXISTS idx_gems_guild_id ON Gems (GuildId);

CREATE INDEX IF NOT EXISTS idx_gems_channel_id ON Gems (ChannelId);

CREATE INDEX IF NOT EXISTS idx_gem_entry_message_author_id ON GemEntry (MessageAuthorId);

CREATE INDEX IF NOT EXISTS idx_gem_entry_message_id ON GemEntry (MessageId);

CREATE INDEX IF NOT EXISTS idx_gem_entry_guild_id ON GemEntry (GuildID);

CREATE INDEX IF NOT EXISTS idx_gem_contributor_user_id ON GemEntry (UserId);

CREATE INDEX IF NOT EXISTS idx_gem_contributor_message_id ON GemEntry (MessageId);

CREATE TABLE IF NOT EXISTS
	GuildHackban (
		SKU UUID DEFAULT gen_random_uuid () PRIMARY KEY,
		UserId BIGINT NOT NULL,
		GuildId BIGINT NOT NULL,
		CreatedOn TIMESTAMP DEFAULT NOW()
	);

CREATE INDEX IF NOT EXISTS idx_hackban_user ON GuildHackban (GuildId, UserId);

CREATE TABLE IF NOT EXISTS DefaultRole (
	SKU UUID DEFAULT gen_random_uuid () PRIMARY KEY,
	GuildId BIGINT,
	RoleId BIGINT NOT NULL,
)

CREATE INDEX IF NOT EXISTS idx_default_role_guild_id ON DefaultRole(GuildId)
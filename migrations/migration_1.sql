-- first port from the java bot

--- **************
	/*  
		main tables
	
		Update 7/12/26: Remove PK mistake from guild_id in guild_user
		
		add feature_blacklist

		add CHECK constraint on xp due to using:
			https://en.wikipedia.org/wiki/Logistic_function#Logistic_differential_equation
	*/
CREATE TABLE IF NOT EXISTS guild (
	guild_id			BIGINT PRIMARY KEY,
	owner_id			BIGINT,
	default_role_id		BIGINT
);
CREATE TABLE IF NOT EXISTS guild_user (
	guild_id 		  	BIGINT,
    user_id 		  	BIGINT,
	xp_asymptote		BIGINT  DEFAULT 200,
	xp 		  			DECIMAL CHECK (xp > 0),
	timezone 		  	TEXT,
	PRIMARY KEY(guild_id, user_id)
);
CREATE TABLE IF NOT EXISTS barred_feature (
	guild_id			BIGINT,
	user_id				BIGINT,
	feature_name		TEXT
);
CREATE TABLE IF NOT EXISTS guild_hackbans (
	guild_id			BIGINT,
	banned_user_id		BIGINT
);
--- **************

--- **************
/*
	gemboard feature tables
*/
CREATE TABLE IF NOT EXISTS guild_gem_giver (
	guild_id			BIGINT,
	user_id				BIGINT,
	contributions		BIGINT DEFAULT 0
);
CREATE TABLE IF NOT EXISTS gem_entry (
	message_id			BIGINT PRIMARY KEY,
	bot_message_id		BIGINT DEFAULT NULL,
	guild_id			BIGINT
);
CREATE TABLE IF NOT EXISTS gemboard (
	guild_id			BIGINT PRIMARY KEY,
	channel_id			BIGINT,
	threshold			BIGINT,
	locked				BOOLEAN
);
--- **************

--- **************
/*
	Admin features,
	first: The builtin permissions are checked (these are hardcoded)
	if the user doesnt posess those permissions then we check these
*/
CREATE TABLE IF NOT EXISTS guild_moderator (
	guild_id							 BIGINT,
	feature_bitfield_value				 BIGINT
);
--- **************
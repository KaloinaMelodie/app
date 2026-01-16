from motor.motor_asyncio import AsyncIOMotorDatabase

async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    # user_id + updated_at_server
    await db["conversations"].create_index(
        [("user_id", 1), ("updated_at_server", -1)],
        name="conv_user_updated_desc"
    )
    # conv_id + updated_at_server
    await db["messages"].create_index(
        [("conv_id", 1), ("updated_at_server", -1)],
        name="msg_conv_updated_desc"
    )
    # dupliquer user_id sur messages pour requete par user
    await db["messages"].create_index(
        [("user_id", 1), ("updated_at_server", -1)],
        name="msg_user_updated_desc"
    )
    # index sur deleted 
    await db["messages"].create_index([("deleted", 1)], name="msg_deleted_flag")
    await db["conversations"].create_index([("deleted", 1)], name="conv_deleted_flag")

    await db["messages"].create_index(
        [("conv_id", 1), ("server_seq", 1)], 
        name="msg_conv_serverseq_asc"
    )
    await db["conversations"].create_index(
        [("user_id", 1), ("server_seq", 1)],
        name="conv_user_serverseq_asc"
    ) 

    await db["admins"].create_index(
        [("email", 1)],
        name="admins_email_unique",
        unique=True,
        partialFilterExpression={"email": {"$exists": True}},
    )

    await db["admins"].create_index(
        [("username", 1)],
        name="admins_username_unique",
        unique=True,
        partialFilterExpression={"username": {"$exists": True}},
    )
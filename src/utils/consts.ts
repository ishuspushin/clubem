export const env = {
    port: process.env.PORT,
    databaseUrl: process.env.DATABASE_URL,
    admin: {
        username: process.env.ADMIN_USERNAME,
        password: process.env.ADMIN_PASSWORD,
    },
    bcrypt: {
        saltRounds: process.env.BCRYPT_SALT_ROUNDS,
    },
}
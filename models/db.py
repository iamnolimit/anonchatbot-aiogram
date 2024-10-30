import asyncpg
import os

class Database:
    async def create(self):
        self.pool = await asyncpg.create_pool(
            database="defaultdb",
            user="avnadmin",
            password="AVNS_7Ig8ZT-GMLhLcutjBxW",
            host="userbot-pg-nolimit-tb.e.aivencloud.com",
            port="25737"
        )
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id BIGINT PRIMARY KEY,
                        age INTEGER,
                        gender VARCHAR
                    );
                ''')

    async def create_user(self, id, age, gender):
        async with self.pool.acquire() as connection:
            await connection.execute(f"INSERT INTO users (id, age, gender) VALUES ('{id}', '{age}', '{gender}')")

    async def check_user(self, id) -> bool:
        async with self.pool.acquire() as con:
            result = await con.fetchval(f"SELECT * FROM users WHERE id = {id} LIMIT 1")
            return bool(result)

    async def get_total_users(self) -> int:
        """Menghitung total user yang terdaftar"""
        async with self.pool.acquire() as con:
            return await con.fetchval("SELECT COUNT(*) FROM users")

    async def get_gender_stats(self) -> dict:
        """Mendapatkan statistik berdasarkan jenis kelamin"""
        async with self.pool.acquire() as con:
            male_count = await con.fetchval("SELECT COUNT(*) FROM users WHERE gender = 'male'")
            female_count = await con.fetchval("SELECT COUNT(*) FROM users WHERE gender = 'female'")
            return {
                'male': male_count,
                'female': female_count
            }

    async def get_age_stats(self) -> dict:
        """Mendapatkan statistik berdasarkan usia"""
        async with self.pool.acquire() as con:
            avg_age = await con.fetchval("SELECT AVG(age) FROM users")
            min_age = await con.fetchval("SELECT MIN(age) FROM users")
            max_age = await con.fetchval("SELECT MAX(age) FROM users")
            return {
                'average': round(avg_age, 1) if avg_age else 0,
                'youngest': min_age or 0,
                'oldest': max_age or 0
            }

    async def get_age_distribution(self) -> dict:
        """Mendapatkan distribusi usia pengguna dalam rentang"""
        async with self.pool.acquire() as con:
            ranges = {
                '<18': 'age < 18',
                '18-25': 'age BETWEEN 18 AND 25',
                '26-35': 'age BETWEEN 26 AND 35',
                '36-50': 'age BETWEEN 36 AND 50',
                '>50': 'age > 50'
            }
            
            distribution = {}
            for label, condition in ranges.items():
                count = await con.fetchval(f"SELECT COUNT(*) FROM users WHERE {condition}")
                distribution[label] = count
            
            return distribution

    async def get_user_stats(self) -> dict:
        """Mendapatkan semua statistik pengguna dalam satu fungsi"""
        total = await self.get_total_users()
        gender_stats = await self.get_gender_stats()
        age_stats = await self.get_age_stats()
        age_dist = await self.get_age_distribution()
        
        return {
            'total_users': total,
            'gender_stats': gender_stats,
            'age_stats': age_stats,
            'age_distribution': age_dist
        }

    @classmethod
    async def get_all_users(cls):
        """Get all user IDs from the database"""
        query = "SELECT user_id FROM users"
        result = await cls.execute(query, fetch=True)
        return [row[0] for row in result] if result else []

DB = Database()

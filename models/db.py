import asyncpg
from typing import List, Dict, Any, Optional

class Database:
    def __init__(self):
        self.pool = None
    
    async def create(self):
        """Initialize the database connection pool and create tables"""
        self.pool = await asyncpg.create_pool(
            database="defaultdb",
            user="avnadmin",
            password="AVNS_7Ig8ZT-GMLhLcutjBxW",
            host="userbot-pg-nolimit-tb.e.aivencloud.com",
            port="25737"
        )
        async with self.pool.acquire() as connection:
            await connection.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    age INTEGER,
                    gender VARCHAR
                );
            ''')

    async def create_user(self, id: int, age: int, gender: str) -> None:
        """Create a new user in the database"""
        async with self.pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO users (id, age, gender) VALUES ($1, $2, $3)",
                id, age, gender
            )

    async def check_user(self, id: int) -> bool:
        """Check if a user exists in the database"""
        async with self.pool.acquire() as connection:
            result = await connection.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)",
                id
            )
            return bool(result)

    async def get_total_users(self) -> int:
        """Count total registered users"""
        async with self.pool.acquire() as connection:
            return await connection.fetchval("SELECT COUNT(*) FROM users")

    async def get_gender_stats(self) -> Dict[str, int]:
        """Get statistics based on gender"""
        async with self.pool.acquire() as connection:
            male_count = await connection.fetchval(
                "SELECT COUNT(*) FROM users WHERE gender = $1",
                'male'
            )
            female_count = await connection.fetchval(
                "SELECT COUNT(*) FROM users WHERE gender = $1",
                'female'
            )
            return {
                'male': male_count or 0,
                'female': female_count or 0
            }

    async def get_age_stats(self) -> Dict[str, float]:
        """Get age-based statistics"""
        async with self.pool.acquire() as connection:
            stats = await connection.fetch("""
                SELECT 
                    ROUND(AVG(age)::numeric, 1) as avg_age,
                    MIN(age) as min_age,
                    MAX(age) as max_age
                FROM users
            """)
            row = stats[0]
            return {
                'average': float(row['avg_age'] or 0),
                'youngest': int(row['min_age'] or 0),
                'oldest': int(row['max_age'] or 0)
            }

    async def get_age_distribution(self) -> Dict[str, int]:
        """Get user age distribution in ranges"""
        async with self.pool.acquire() as connection:
            distribution = await connection.fetch("""
                SELECT 
                    CASE 
                        WHEN age < 18 THEN '<18'
                        WHEN age BETWEEN 18 AND 25 THEN '18-25'
                        WHEN age BETWEEN 26 AND 35 THEN '26-35'
                        WHEN age BETWEEN 36 AND 50 THEN '36-50'
                        ELSE '>50'
                    END as age_range,
                    COUNT(*) as count
                FROM users
                GROUP BY age_range
                ORDER BY age_range
            """)
            return {row['age_range']: row['count'] for row in distribution}

    async def get_user_stats(self) -> Dict[str, Any]:
        """Get all user statistics in one call"""
        async with self.pool.acquire() as connection:
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

    async def get_all_users(self) -> List[int]:
        """Get all user IDs from the database"""
        async with self.pool.acquire() as connection:
            rows = await connection.fetch("SELECT id FROM users")
            return [row['id'] for row in rows]

# Create a single instance
DB = Database()

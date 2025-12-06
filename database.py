import sqlite3
import datetime
import os
from typing import List, Dict, Optional

class SentimentDatabase:
    def __init__(self, db_path: str = "data/sentiment.db"):

        self.db_path = db_path
        self._init_database()

    def _get_connection(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS sentiment_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT NOT NULL,
            cleaned_text TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            confidence REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        create_index_sql = """
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON sentiment_records(timestamp DESC)
        """

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                cursor.execute(create_index_sql)
                conn.commit()
            print(f"✅ Database đã sẵn sàng: {self.db_path}")
        except Exception as e:
            print(f"❌ Lỗi khởi tạo database: {e}")
            raise

    def save_record(self,
                    original_text: str,
                    cleaned_text: str,
                    sentiment: str,
                    confidence: float) -> bool:

        insert_sql = """
        INSERT INTO sentiment_records 
        (original_text, cleaned_text, sentiment, confidence, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_sql,
                               (original_text, cleaned_text, sentiment, confidence, timestamp))
                conn.commit()
            return True
        except Exception as e:
            print(f"❌ Lỗi khi lưu record: {e}")
            return False

    def get_recent_records(self, limit: int = 50) -> List[Dict]:

        select_sql = """
        SELECT * FROM sentiment_records 
        ORDER BY timestamp DESC 
        LIMIT ?
        """

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(select_sql, (limit,))
                rows = cursor.fetchall()

                records = []
                for row in rows:
                    records.append({
                        "id": row["id"],
                        "original_text": row["original_text"],
                        "cleaned_text": row["cleaned_text"],
                        "sentiment": row["sentiment"],
                        "confidence": row["confidence"],
                        "timestamp": row["timestamp"]
                    })
                return records
        except Exception as e:
            print(f"❌ Lỗi khi lấy records: {e}")
            return []

    def get_all_records(self) -> List[Dict]:

        return self.get_recent_records(limit=1000)

    def get_statistics(self) -> Dict:

        stats_sql = """
        SELECT 
            COUNT(*) as total,
            AVG(confidence) as avg_confidence,
            SUM(CASE WHEN sentiment = 'POSITIVE' THEN 1 ELSE 0 END) as positive_count,
            SUM(CASE WHEN sentiment = 'NEUTRAL' THEN 1 ELSE 0 END) as neutral_count,
            SUM(CASE WHEN sentiment = 'NEGATIVE' THEN 1 ELSE 0 END) as negative_count
        FROM sentiment_records
        """

        sentiment_counts_sql = """
        SELECT sentiment, COUNT(*) as count
        FROM sentiment_records
        GROUP BY sentiment
        ORDER BY count DESC
        """

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(stats_sql)
                stats_row = cursor.fetchone()

                cursor.execute(sentiment_counts_sql)
                sentiment_rows = cursor.fetchall()

                sentiment_counts = {}
                for row in sentiment_rows:
                    sentiment_counts[row["sentiment"]] = row["count"]

                return {
                    "total_records": stats_row["total"] if stats_row else 0,
                    "avg_confidence": round(stats_row["avg_confidence"], 3) if stats_row and stats_row[
                        "avg_confidence"] else 0,
                    "positive_count": stats_row["positive_count"] if stats_row else 0,
                    "neutral_count": stats_row["neutral_count"] if stats_row else 0,
                    "negative_count": stats_row["negative_count"] if stats_row else 0,
                    "sentiment_counts": sentiment_counts
                }
        except Exception as e:
            print(f"❌ Lỗi khi lấy thống kê: {e}")
            return {
                "total_records": 0,
                "avg_confidence": 0,
                "positive_count": 0,
                "neutral_count": 0,
                "negative_count": 0,
                "sentiment_counts": {}
            }

    def delete_old_records(self, days_old: int = 30) -> int:

        delete_sql = """
        DELETE FROM sentiment_records 
        WHERE timestamp < datetime('now', ?)
        """

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(delete_sql, (f'-{days_old} days',))
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count
        except Exception as e:
            print(f"❌ Lỗi khi xóa records cũ: {e}")
            return 0

    def export_to_csv(self, csv_path: str = "sentiment_export.csv") -> bool:

        import csv

        try:
            records = self.get_all_records()

            if not records:
                print("⚠️ Không có dữ liệu để export")
                return False

            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'original_text', 'cleaned_text',
                              'sentiment', 'confidence', 'timestamp']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for record in records:
                    writer.writerow(record)

            print(f"✅ Đã export {len(records)} records ra {csv_path}")
            return True

        except Exception as e:
            print(f"❌ Lỗi khi export CSV: {e}")
            return False

    def close(self):

        pass

# TEST MODULE
if __name__ == "__main__":
    print("🧪 Testing SentimentDatabase...")

    db = SentimentDatabase("data/test_sentiment.db")

    test_data = [
        {
            "original": "Hôm nay tôi rất vui",
            "cleaned": "hôm nay tôi rất vui",
            "sentiment": "POSITIVE",
            "confidence": 0.98
        },
        {
            "original": "Món ăn dở quá",
            "cleaned": "món ăn dở quá",
            "sentiment": "NEGATIVE",
            "confidence": 0.92
        }
    ]

    print("\n💾 Testing save_record...")
    for data in test_data:
        success = db.save_record(
            data["original"],
            data["cleaned"],
            data["sentiment"],
            data["confidence"]
        )
        print(f"  - Lưu '{data['original'][:20]}...': {'✅' if success else '❌'}")

    print("\n📄 Testing get_recent_records...")
    records = db.get_recent_records(5)
    print(f"  - Số records: {len(records)}")
    for i, record in enumerate(records, 1):
        print(f"    {i}. {record['cleaned_text'][:30]}... [{record['sentiment']}]")

    print("\n📊 Testing get_statistics...")
    stats = db.get_statistics()
    print(f"  - Tổng records: {stats['total_records']}")
    print(f"  - Confidence trung bình: {stats['avg_confidence']:.3f}")
    print(f"  - Phân bố sentiment: {stats['sentiment_counts']}")

    import os

    if os.path.exists("data/test_sentiment.db"):
        os.remove("data/test_sentiment.db")
        os.rmdir("data")

    print("\n✅ Database testing hoàn tất!")

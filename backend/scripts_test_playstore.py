from src.service.playstore import search_playstore


if __name__ == "__main__":
    app_id = "com.nu.production"
    for i, r in enumerate(search_playstore(app_id, max_reviews=30, headless=True), start=1):
        print(f"#{i} rating={r.rating} date={r.date} author={r.author}")
        print(r.text[:200].replace("\n", " "))
        print("-")

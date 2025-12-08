from database import backup_sensor_data, restore_sensor_data, seed_fake_week

if __name__ == "__main__":
    # 1. Back up what you have now
    backup_sensor_data()

    # 2. Seed the DB with a full week's worth of fake samples
    seed_fake_week()

    # Later, when you’re done testing, run this script again
    # and comment out seed_fake_week() and call restore instead:
    # restore_sensor_data()

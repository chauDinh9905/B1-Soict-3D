-- Chỉ chạy MỘT lần khi volume pgdata được tạo lần đầu. Đã có volume cũ thì: docker compose down -v
CREATE DATABASE tour_test OWNER tour;

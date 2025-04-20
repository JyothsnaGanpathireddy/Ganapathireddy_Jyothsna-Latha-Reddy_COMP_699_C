-- -- phpMyAdmin SQL Dump
-- -- version 5.2.1
-- -- https://www.phpmyadmin.net/
-- --
-- -- Host: 127.0.0.1
-- -- Generation Time: Feb 02, 2025 at 06:08 AM
-- -- Server version: 10.4.32-MariaDB
-- -- PHP Version: 8.2.12

-- SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
-- START TRANSACTION;
-- SET time_zone = "+00:00";


-- /*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
-- /*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
-- /*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
-- /*!40101 SET NAMES utf8mb4 */;

-- --
-- -- Database: `pharmacy_db`
-- --

-- -- --------------------------------------------------------

-- --
-- -- Table structure for table `inventory`
-- --

-- CREATE TABLE `inventory` (
--   `id` int(11) NOT NULL,
--   `name` varchar(250) NOT NULL,
--   `emailname` varchar(255) NOT NULL,
--   `batchId` varchar(100) NOT NULL,
--   `stock` varchar(100) NOT NULL,
--   `expireDate` date NOT NULL,
--   `price` varchar(100) NOT NULL,
--   `image` varchar(255) NOT NULL,
--   `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
--   `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --
-- -- Dumping data for table `inventory`
-- --

-- INSERT INTO `inventory` (`id`, `name`, `emailname`, `batchId`, `stock`, `expireDate`, `price`, `image`, `created_at`, `updated_at`) VALUES
-- (1, 'q', 'ak@gmail.com', '12343', '7', '3444-03-12', '300', 'images/logo.png', '2025-02-01 05:54:22', '2025-02-01 09:33:57'),
-- (3, 'w', '1@gmail.com', 'AT001', '7', '2025-02-01', '400', 'images/Screenshot_1013.png', '2025-02-01 06:53:04', '2025-02-01 09:34:00'),
-- (4, 'e', '2@gmail.com', 'AT002', '8', '2025-02-08', '350', 'images/Screenshot_1014.png', '2025-02-01 06:53:27', '2025-02-01 09:34:02'),
-- (5, 't', '3@gmail.com', 'AT003', '2', '2025-02-23', '300', 'images/Screenshot_1015.png', '2025-02-01 06:53:47', '2025-02-01 09:34:05'),
-- (6, 'y', '4@gmail.com', 'AT004', '1', '2025-02-23', '300', 'images/Screenshot_1023.png', '2025-02-01 06:54:05', '2025-02-01 09:34:10'),
-- (7, 'u', '5@gmail.com', 'AT005', '3', '2025-03-08', '500', 'images/Screenshot_1023.png', '2025-02-01 06:54:29', '2025-02-01 09:34:12'),
-- (8, 'a', '7@gmail.com', 'AT008', '2', '2025-02-02', '300', 'images/Screenshot_1022.png', '2025-02-01 07:49:27', '2025-02-01 07:49:27'),
-- (9, 'check', 'ak@gmail.com', '12343', '2', '2025-02-20', '300', 'images/Screenshot_1023.png', '2025-02-01 12:38:29', '2025-02-01 12:38:29'),
-- (10, 'test', '4@gmail.com', 'AT001', '2', '2025-02-06', '300', 'images/Screenshot_1029.png', '2025-02-01 12:39:06', '2025-02-01 12:39:06'),
-- (11, 'q', 'shriihaz@gmail.com', 'N/A', '1', '2099-12-31', '300', 'images/logo.png', '2025-02-01 16:38:54', '2025-02-01 16:38:54');

-- -- --------------------------------------------------------

-- --
-- -- Table structure for table `orders`
-- --

-- CREATE TABLE `orders` (
--   `id` int(11) NOT NULL,
--   `user_id` int(11) DEFAULT NULL,
--   `item_id` int(11) DEFAULT NULL,
--   `created_at` timestamp NOT NULL DEFAULT current_timestamp()
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --
-- -- Dumping data for table `orders`
-- --

-- INSERT INTO `orders` (`id`, `user_id`, `item_id`, `created_at`) VALUES
-- (2, 1, 1, '2025-02-01 16:15:01'),
-- (3, 1, 3, '2025-02-01 16:15:01');

-- -- --------------------------------------------------------

-- --
-- -- Table structure for table `sales`
-- --

-- CREATE TABLE `sales` (
--   `id` int(11) NOT NULL,
--   `name` varchar(255) DEFAULT NULL,
--   `number` varchar(20) DEFAULT NULL,
--   `email` varchar(255) DEFAULT NULL,
--   `medicine` varchar(255) DEFAULT NULL,
--   `cost` decimal(10,2) DEFAULT NULL,
--   `created_at` timestamp NOT NULL DEFAULT current_timestamp()
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --
-- -- Dumping data for table `sales`
-- --

-- INSERT INTO `sales` (`id`, `name`, `number`, `email`, `medicine`, `cost`, `created_at`) VALUES
-- (1, 'hey', '9988776655', 'aislynitdepartment@gmail.com', 'para', 300.00, '2025-02-01 12:28:44'),
-- (2, 'Unknown', 'N/A', 'shriihaz@gmail.com', 'e', 350.00, '2025-02-01 16:53:26'),
-- (3, 'Unknown', 'N/A', 'shriihaz@gmail.com', 't', 300.00, '2025-02-01 16:53:26'),
-- (4, 'Unknown', 'N/A', 'shriihaz@gmail.com', 'q', 300.00, '2025-02-01 16:53:26'),
-- (5, 'Unknown', 'N/A', 'shriihaz@gmail.com', 'w', 400.00, '2025-02-01 16:56:00'),
-- (6, 'test', '6360355357', 'shriihaz@gmail.com', 't', 300.00, '2025-02-01 16:56:51'),
-- (7, 'test', '6360355357', 'shriihaz@gmail.com', 'e', 350.00, '2025-02-01 17:08:11'),
-- (8, 'test', '6360355357', 'shriihaz@gmail.com', 'w', 400.00, '2025-02-01 17:08:11'),
-- (9, 'test', '6360355357', 'shriihaz@gmail.com', 'q', 300.00, '2025-02-01 17:11:21'),
-- (10, 'test', '6360355357', 'shriihaz@gmail.com', 'w', 400.00, '2025-02-01 17:12:27'),
-- (11, 'test', '6360355357', 'shriihaz@gmail.com', 'e', 350.00, '2025-02-02 05:04:09'),
-- (12, 'user', '9988776655', 'aislynitdepartment@gmail.com', 'para', 200.00, '2025-02-02 05:06:06');

-- -- --------------------------------------------------------

-- --
-- -- Table structure for table `users`
-- --

-- CREATE TABLE `users` (
--   `id` int(11) NOT NULL,
--   `name` varchar(255) NOT NULL,
--   `email` varchar(255) NOT NULL,
--   `number` varchar(20) NOT NULL,
--   `role` enum('Pharmacist','User') NOT NULL,
--   `password` varchar(255) NOT NULL,
--   `created_at` timestamp NOT NULL DEFAULT current_timestamp()
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --
-- -- Dumping data for table `users`
-- --

-- INSERT INTO `users` (`id`, `name`, `email`, `number`, `role`, `password`, `created_at`) VALUES
-- (1, 'Ajaycode', 'ajaydloner@gmail.com', '7373327552', 'Pharmacist', 'scrypt:32768:8:1$cktc7j6dnjLcWxcG$a184ca041c03a84b45033181b3110542930df151fb5f117710d871651fb80a916791d9573485ea22cc54aa7ed4a281e859908ebfb30ed7ff7e777f0d6911c5e5', '2025-02-01 04:08:08'),
-- (2, 'test', 'shriihaz@gmail.com', '6360355357', 'User', 'scrypt:32768:8:1$z5Qn3w2RZ6O2q6AB$094e34b77073fd05e59a06a1af0b284d235dffe415aa219569235d42cf0d77649044935c23b80c00c919b16c750b28334c29e5e8638d20a589d9fcde23fb02e1', '2025-02-01 04:27:30'),
-- (3, 'noor', 'noorsakina19@gmail.com', '9480318967', 'Pharmacist', 'scrypt:32768:8:1$fUE0bc0QpP3948hm$ad314f5a5f2b9aff81f2b4ef41f301e0901ae79ddb6eec33ca1fa16ba8123604eff6be6ba6196a1ec4ebb980cc902d06bd57ea1f3f7f362acfbfb6f3096d36c4', '2025-02-01 10:08:26');

-- --
-- -- Indexes for dumped tables
-- --

-- --
-- -- Indexes for table `inventory`
-- --
-- ALTER TABLE `inventory`
--   ADD PRIMARY KEY (`id`);

-- --
-- -- Indexes for table `orders`
-- --
-- ALTER TABLE `orders`
--   ADD PRIMARY KEY (`id`),
--   ADD KEY `item_id` (`item_id`);

-- --
-- -- Indexes for table `sales`
-- --
-- ALTER TABLE `sales`
--   ADD PRIMARY KEY (`id`);

-- --
-- -- Indexes for table `users`
-- --
-- ALTER TABLE `users`
--   ADD PRIMARY KEY (`id`),
--   ADD UNIQUE KEY `email` (`email`),
--   ADD UNIQUE KEY `number` (`number`);

-- --
-- -- AUTO_INCREMENT for dumped tables
-- --

-- --
-- -- AUTO_INCREMENT for table `inventory`
-- --
-- ALTER TABLE `inventory`
--   MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

-- --
-- -- AUTO_INCREMENT for table `orders`
-- --
-- ALTER TABLE `orders`
--   MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

-- --
-- -- AUTO_INCREMENT for table `sales`
-- --
-- ALTER TABLE `sales`
--   MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

-- --
-- -- AUTO_INCREMENT for table `users`
-- --
-- ALTER TABLE `users`
--   MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

-- --
-- -- Constraints for dumped tables
-- --

-- --
-- -- Constraints for table `orders`
-- --
-- ALTER TABLE `orders`
--   ADD CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `inventory` (`id`);
-- COMMIT;

-- /*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
-- /*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
-- /*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;




-- table for inventory 
 
CREATE TABLE inventory (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    category VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock INT(10) NOT NULL,
    image VARCHAR(255) NULL
);

-- table for users

CREATE TABLE users (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NULL,
    email VARCHAR(100) UNIQUE NULL,
    number VARCHAR(20) UNIQUE NULL,
    password VARCHAR(255) NULL
);

-- table for orders

CREATE TABLE orders (
    order_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    product_id INT NULL,
    quantity INT NULL,
    total_amount DECIMAL(10,2) NULL,
    sale_date TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    delivery_date TIMESTAMP NULL,
    address TEXT NULL,
    status VARCHAR(50) NULL DEFAULT 'Pending',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES stock(id) ON DELETE CASCADE
);


-- table for reviews

CREATE TABLE reviews (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    user VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    rating INT NULL,
    description VARCHAR(500) NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES stock(id) ON DELETE CASCADE
);

-- table for login_history

CREATE TABLE login_history (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    login_time TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45) NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- table for purchases

CREATE TABLE purchases (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    purchase_date TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- table for wishlist

CREATE TABLE wishlist (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

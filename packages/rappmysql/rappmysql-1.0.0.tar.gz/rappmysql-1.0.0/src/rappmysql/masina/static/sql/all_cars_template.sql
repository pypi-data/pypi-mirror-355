DROP TABLE IF EXISTS `all_cars`;

CREATE TABLE `all_cars` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `tstamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `cartype` varchar(50) NOT NULL,
  `brand` varchar(50) NOT NULL,
  `model` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE `all_cars`
  ADD PRIMARY KEY (`id`),
  ADD KEY `all_cars_users` (`user_id`);

ALTER TABLE `all_cars`
  ADD CONSTRAINT `all_cars_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;
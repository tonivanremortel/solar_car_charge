SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

CREATE TABLE `meter` (
  `datetime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `power` int DEFAULT NULL COMMENT 'power available at measurement',
  `export` int UNSIGNED NOT NULL DEFAULT '0' COMMENT 'Snapshot of meter in Wh',
  `import` int UNSIGNED NOT NULL DEFAULT '0' COMMENT 'Snapshot of meter in Wh'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

CREATE TABLE `settings` (
  `topic` varchar(50) NOT NULL,
  `value` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

ALTER TABLE `meter`
  ADD PRIMARY KEY (`datetime`);

ALTER TABLE `settings`
  ADD PRIMARY KEY (`topic`,`value`);
COMMIT;

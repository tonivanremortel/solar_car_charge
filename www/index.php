<?php

$db_host = "localhost";
$db_user = "user";
$db_pass = "pwd";
$db_db = "solar_car_charge";

$link = mysqli_connect($db_host, $db_user, $db_pass, $db_db);

# Post any change
if ( $_SERVER["REQUEST_METHOD"] == "POST" )
{
	$rcv_status = $_POST["flip-status"];
	( $rcv_status == 'on' ) ? $status = 1 : $status = 0;
	$sql = "update settings set value='$status' where topic='active'";
	$res = mysqli_query($link, $sql);

	$rvc_power = ceil($_POST["slider"]*690);
	$sql = "update settings set value='$rvc_power' where topic='minimal_kwh_to_start_charging'";
	$res = mysqli_query($link, $sql);
}


# Get settings
$sql = "select topic,value from settings";
$res = mysqli_query($link, $sql);
while ( $row = mysqli_fetch_assoc($res) )
{
	$settings[$row['topic']] = $row['value'];
}
$status = $settings['active'];

$min_power_amp = ceil($settings['minimal_kwh_to_start_charging']/690);

# Get P1 info
$sql = "SELECT * FROM `meter` order by `datetime` desc limit 3";
$res = mysqli_query($link, $sql);
while ( $row = mysqli_fetch_assoc($res) )
{
	$p1_export[] = $row["export"];
	$p1_import[] = $row["import"];
	$p1[] = $row["power"];
	$p1_avg = ($p1_avg + $row["power"])/2;
	$p1_avg_amp = ceil(abs($p1_avg/690));
}
$avg_p1_export = ($p1_export[0] - $p1_export[2]) / 2 * 60;
$amp_p1_export = ceil(abs($avg_p1_export/690));
$avg_p1_import = ($p1_import[0] - $p1_import[2]) / 2 * 60;
$amp_p1_import = ceil(abs($avg_p1_import/690));

?>
<html>
<head>
	<title>Solar Car Charge</title>
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<link rel="stylesheet" href="http://fonts.googleapis.com/css?family=Open+Sans:300,400,700">
	<link rel="stylesheet" href="http://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.css" />
	<script src="http://code.jquery.com/jquery-1.11.1.min.js"></script>
	<script src="http://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.js"></script>
</head>
<body>
<div data-role="page">

	<div data-role="header">
		<h1>Solar Car Charge</h1>
	</div>
	<div data-role="content">	
		<form method="post" action="<?=$_SERVER['PHP_SELF']?>">
			<p>Status: <input type="checkbox" data-role="flipswitch" name="flip-status" id="flip-status" <?php if ($status == 1) { print('checked=""'); } ?> ></p>
			<p>Min power (A): <input type="range" name="slider" id="slider" value="<?=$min_power_amp?>" min="3" max="12"></p>
			<p><input type="submit" value="Submit"></p>
		</form>
	</div>
	<div data-role="content">
		<p>Export: <?=$avg_p1_export?> W (<?=$amp_p1_export?> A)</p>
		<p>Import: <?=$avg_p1_import?> W (<?=$amp_p1_import?> A)</p>
	</div>
</div>
</body>
</html>

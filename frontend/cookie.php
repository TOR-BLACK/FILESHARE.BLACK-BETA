<?php
	$cookie_name = $_GET['cookie'];
	$cookie_value = $_GET['value'];
	$url = $_GET['url'];
	setcookie($cookie_name, $cookie_value, time() + (86400 * 365));

	header("Location: note/" . $url);
?>
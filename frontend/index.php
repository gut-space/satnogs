<!DOCTYPE html>
<html lang="en">
<head>
  <title>SATNOGS-GDN Project</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css">
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js"></script>
  <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js"></script>
</head>
<body>

<div class="container">
  <h2>SATNOGS-GDN</h2>
  <p>This is a Gdańsk ground station, aiming to join the global network of satellite ground-stations.
  It's a project created by Sławek Figiel, Tomek Mrugalski and Ewelina Omernik, three students of
  Space and Satellite Technologies studies of Gdańsk University of Technology.</p>


<?php

function showStats($dbconn) {
    $result = pg_query("SELECT count(*) FROM observations") or die('Query failed: ' . pg_last_error());
    $obsCnt = pg_fetch_row($result, 0) [0];
    pg_free_result($result);

    $result = pg_query("SELECT count(distinct sat_name) FROM observations") or die('Query failed: ' . pg_last_error());
    $satsCnt = pg_fetch_row($result, 0) [0];
    pg_free_result($result);

    $result = pg_query("SELECT min(aos), max(aos) FROM observations") or die('Query failed: ' . pg_last_error());
    $row = pg_fetch_row($result, 0);
    $startDate = $row[0];
    $endDate   = $row[1];
    pg_free_result($result);

    echo "<p> $obsCnt observations from $satsCnt sattelite(s), between $startDate and $endDate.</p>";
}

function showSats($dbconn) {
    // Performing SQL query
    $query = 'SELECT * FROM satellites';
    $result = pg_query($query) or die('Query failed: ' . pg_last_error());

    // Printing results in HTML
    $cnt = 0;
    echo "<h3>Satellites</h3>";
    echo "<table class='table table-striped'>\n";
    echo "<tr><th>ID</th><th>Name</th></tr>";
    while ($line = pg_fetch_array($result, null, PGSQL_ASSOC)) {
        echo "\t<tr>\n";
        echo "<td>" . $line["sat_id"] . "</td>";
        echo "<td><a href=\"". $line["url"]. "\">". $line["sat_name"] . "</a></td>";

        //var_dump($line);
        //foreach ($line as $col_value) {
        //    echo "\t\t<td>$col_value</td>\n";
        //}
        echo "\t</tr>\n";
        $cnt++;
    }
    echo "</table>\n";

    // Free resultset
    pg_free_result($result);
}

function showObservations($dbconn) {
        echo "<h3>Observations</h3>";
        $query = 'SELECT * FROM observations';
        $result = pg_query($query) or die('Query failed: ' . pg_last_error());

        // Printing results in HTML
        $cnt = 0;
        echo "<table class='table table-striped table-hover'>\n";
        echo "<tr><th>obs_id</th><th>aos</th><th>tca</th><th>los</th><th>sat_id</th><th>sat_name</th><th>filename</th><th>notes</th></tr>";
        while ($line = pg_fetch_array($result, null, PGSQL_ASSOC)) {
            echo "\t<tr>\n";
            echo "<td>" . $line["obs_id"] . "</td>";
            echo "<td>" . $line["aos"] . "</td>";
            echo "<td>" . $line["tca"] . "</td>";
            echo "<td>" . $line["los"] . "</td>";
            echo "<td>" . $line["sat_id"] . "</td>";
            echo "<td>" . $line["sat_name"] . "</td>";
            echo "<td><a href=\"data/" . $line["filename"] . "\">" . $line["filename"] . "</a></td>";
            echo "<td>" . $line["notes"] . "</td>";
            //foreach ($line as $col_value) {
            //    echo "\t\t<td>$col_value</td>\n";
            //}
            echo "\t</tr>\n";
            $cnt++;
        }
        echo "</table>\n";

    // Free result set
    pg_free_result($result);
}

// Connecting, selecting database
$dbconn = pg_connect("host=localhost dbname=satnogs user=satnogs password=lie8Avie")
    or die('Could not connect: ' . pg_last_error());

showStats($dbconn);

showObservations($dbconn);

showSats($dbconn);

// Closing connection
pg_close($dbconn);



?>
</div>
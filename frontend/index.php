Satnogs boilerplate page.

Yup, it's in PHP. It's temporary. We will come up with a real one in Angular + some backend in python.

<?php 

// Connecting, selecting database
$dbconn = pg_connect("host=localhost dbname=satnogs user=satnogs password=lie8Avie")
    or die('Could not connect: ' . pg_last_error());

// Performing SQL query
$query = 'SELECT * FROM satellites';
$result = pg_query($query) or die('Query failed: ' . pg_last_error());

// Printing results in HTML
$cnt = 0;
echo "<h3>Satellites</h3>";
echo "<table>\n";
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
echo "$cnt satellite(s).<br/>\n";

// Free resultset
pg_free_result($result);


echo "<h3>Observations</h3>";
$query = 'SELECT * FROM observations';
$result = pg_query($query) or die('Query failed: ' . pg_last_error());

// Printing results in HTML
$cnt = 0;
echo "<table>\n";
echo "<tr><th>obs_id</th><th>aos</th><th>tca</th><th>los</th><th>sat_id</th><th>sat_name</th><th>filename</th><th>notes</th></tr>";
while ($line = pg_fetch_array($result, null, PGSQL_ASSOC)) {
    echo "\t<tr>\n";
    echo "<td>" . $line["obs_id"] . "</td>";
    echo "<td>" . $line["aos"] . "</td>";
    echo "<td>" . $line["tca"] . "</td>";
    echo "<td>" . $line["los"] . "</td>";
    echo "<td>" . $line["sat_id"] . "</td>";
    echo "<td>" . $line["sat_name"] . "</td>";
    echo "<td><a href=\"" . $line["filename"] . "\">" . $line["filename"] . "</a></td>";
    echo "<td>" . $line["notes"] . "</td>";
    //foreach ($line as $col_value) {
    //    echo "\t\t<td>$col_value</td>\n";
    //}
    echo "\t</tr>\n";
    $cnt++;
}
echo "</table>\n";

echo "$cnt++ observation(s).<br>\n";

// Free resultset
pg_free_result($result);


// Closing connection
pg_close($dbconn);



?>

<?php
// start index.php
function getFullSource($filename){
    $included = array();
    $original = file_get_contents($filename);
    $basePath = dirname($filename)."/";
    preg_match_all("/(\s*(include|require)(_once)?\s*\(?(.*?)\)?;)/", $original, $queue, PREG_SET_ORDER);
    while (count($queue) > 0){
        $val = array_shift($queue);
        $file_val = $val[4];
        $file_val = str_replace(array("dirname(__FILE__)", "__DIR__"), "", $file_val);
        $file = trim(str_replace(array("'",'"',';',')'),"",$file_val));
        $include_once = strlen($val[3]) > 0;
        if ($include_once) {
            $file = trim(str_replace(array("'",'"',';',')'),"",$file_val));
        }

        $content = "?>".trim(@file_get_contents($basePath.$file))."?><?php";

        if($include_once && in_array($file,$included)) {
            $content = "";
        }

        if (file_exists($basePath.$file) && !in_array($file,$included)) {
            array_push($included,$file);
        }
        preg_match_all("/(\s*(include|require)(_once)?\s*\(?(.*)\)?;?)/", $content, $matches, PREG_SET_ORDER);

        if (!@file_exists($basePath.$file)) {
            $content = $val[0];
        }
        $original = str_replace($val[0],$content,$original);
        $queue = array_merge($queue,$matches);
    #print substr($original,strpos($original,"include"));
    }
    return $original;
}
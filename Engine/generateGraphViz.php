<?php
require "./php-cfg/vendor/autoload.php";
use PhpParser\ParserFactory;
$parser = new PHPCfg\Parser((new ParserFactory)->create(ParserFactory::PREFER_PHP7));

$declarations = new PHPCfg\Visitor\DeclarationFinder;
$calls = new PHPCfg\Visitor\CallFinder;
$variables = new PHPCfg\Visitor\VariableFinder;

$traverser = new PHPCfg\Traverser;
$traverser->addVisitor($declarations);
$traverser->addVisitor($calls);
$traverser->addVisitor(new PHPCfg\Visitor\Simplifier);
$traverser->addVisitor($variables);

$filename = $argv[1];

$code = file_get_contents($filename);
$block = $parser->parse($code, $filename);
$traverser->traverse($block);

$printer = new PHPCfg\Printer\Text;
print $printer->printScript($block);
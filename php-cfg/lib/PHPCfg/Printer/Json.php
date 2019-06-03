<?php

/*
 * This file is part of PHP-CFG, a Control flow graph implementation for PHP
 *
 * @copyright 2015 Anthony Ferrara. All rights reserved
 * @license MIT See LICENSE at the root of the project for more info
 */

namespace PHPCfg\Printer;

use PHPCfg\Func;
use PHPCfg\Printer;
use PHPCfg\Script;
use phpDocumentor\GraphViz\Edge;
use phpDocumentor\GraphViz\Graph;
use phpDocumentor\GraphViz\Node;

class Json extends Printer {
    public function printScript(Script $script) {
        $output['main']=$this->printCFG($script->main);
        foreach ($script->functions as $func) {
            $scope = $func->class ? $func->class->value . '::' : '';
            $name = "$scope$func->name()";
            $output[$name] = $this->printCFG($func);
        }
        return $output;
    }

    public function printFunc(Func $func) {
    }

    protected function renderVar(\PHPCfg\Operand $var) {
        $type = isset($var->type) ? "<{$var->type}>" : "";
        $result = array();
        if (!empty($type)){
            $result['type'] = $type;
        }
        if (property_exists($var,"byRef")){
            $result['byRef'] = $var->byRef;
        }
        if ($var instanceof \PHPCfg\Operand\Literal) {
            $result['value'] = "LITERAL{$type}(" . var_export($var->value, true) . ")";
        } elseif ($var instanceof \PHPCfg\Operand\Variable) {
            if ($var instanceof \PHPCfg\Operand\BoundVariable) {
                switch ($var->scope) {
                    case \PHPCfg\Operand\BoundVariable::SCOPE_GLOBAL:
                    $result['scope'] = "global";
                    break;
                    case \PHPCfg\Operand\BoundVariable::SCOPE_LOCAL:
                    $result['scope'] = "local";
                    break;
                    case \PHPCfg\Operand\BoundVariable::SCOPE_OBJECT:
                    $result['scope'] = "this";
                    break;
                    case \PHPCfg\Operand\BoundVariable::SCOPE_FUNCTION:
                    $result['scope'] = "static";
                    break;
                    default:
                    throw new \LogicException("Unknown bound variable scope");
                }
            }
            $result['var_name'] = $var->name->value;
        } elseif ($var instanceof \PHPCfg\Operand\Temporary) {
            $id = $this->getVarId($var);
            $result['id'] = "$id";
            if ($var->original) {
                $result = array_merge($result,$this->renderVar($var->original));
            }
        } elseif (is_array($var)) {
            $result['type'] = "array$type";
            foreach ($var as $k => $v) {
                $result['vars'][$k] = $this->renderVar($v);
            }
        }
        return $result;
    }

    protected function renderOp(\PHPCfg\Op $op) {
        $result['op'] = $op->getType();
        if ($op instanceof \PHPCfg\Op\CallableOp) {
            $result['opName'] = (String) $op->getFunc()->name;
        }
        if ($op instanceof \PHPCfg\Op\Expr\Assertion) {
            $result['assertion'] = $this->renderAssertion($op->assertion);
        }  
        foreach ($op->getVariableNames() as $varName) {
            $vars = $op->$varName;
            if (is_array($vars)) {
                foreach ($vars as $key => $var) {
                    if (!$var) {
                        continue;
                    }
                    $result[$varName][$key] = str_replace(array("\n","\r",'"'),array('\\\\n','\\\\r','\\"'),$this->renderVar($var));
                }
            } elseif ($vars) {
                $result[$varName] = str_replace(array("\n","\r",'"'),array('\\\\n','\\\\r','\\"'),$this->renderVar($vars));
            }
        }
        $childBlocks = [];
        foreach ($op->getSubBlocks() as $blockName) {
            $sub = $op->$blockName;
            if (is_null($sub)) {
                continue;
            }
            if (!is_array($sub)) {
                $sub = [$sub];
            }
            foreach ($sub as $subBlock) {
                if (!$subBlock) {
                    continue;
                }
                $this->enqueueBlock($subBlock);
                $childBlocks[] = [
                "block" => $subBlock,
                "name"  => $blockName,
                ];
            }
        }
        return [
        "op"          => $op,
        "label"       => $result,
        "attributes"  => $op->getAttributes(),
        "childBlocks" => $childBlocks,
        ];
    }

    protected function render(Func $func) {
        if ($func->cfg) {
            $this->enqueueBlock($func->cfg);
        }
        $renderedOps = new \SplObjectStorage;
        $renderedBlocks = new \SplObjectStorage;

        while ($this->blockQueue->count() > 0) {
            $block = $this->blockQueue->dequeue();
            $ops = [];
            if ($block === $func->cfg) {
                foreach ($func->params as $param) {
                    $renderedOps[$param] = $ops[] = $this->renderOp($param);
                }
            }
            foreach ($block->phi as $phi) {
                $result = $this->indent($this->renderOperand($phi->result) . " = Phi(");
                $result .= implode(', ', array_map([$this, 'renderOperand'], $phi->vars));
                $result .= ')';
                $renderedOps[$phi] = $ops[] = [
                    "op"          => $phi,
                    "label"       => array("op"=>$result,"result" => $this->renderVar($phi->result),"vars" =>array_map([$this, 'renderVar'], $phi->vars)),
                    "childBlocks" => [],
                    ];
            }
            foreach ($block->children as $child) {
                $renderedOps[$child] = $ops[] = $this->renderOp($child);
            }
            $renderedBlocks[$block] = $ops;
        }
        $varIds = $this->varIds;
        $blockIds = $this->blocks;
        $this->reset();
        return [
        "blocks"   => $renderedBlocks,
        "ops"      => $renderedOps,
        "varIds"   => $varIds,
        "blockIds" => $blockIds,
        ];
    }

    public function printCFG(Func $blocks) {
        $rendered = $this->render($blocks);
        $blocks = array();
        foreach ($rendered['blocks'] as $block) {
            $ops = $rendered['blocks'][$block];
            $block_ = array();
            $block_['parentBlock'] = array();
            foreach ($block->parents as $prev) {
                if ($rendered['blockIds']->contains($prev)) {
                    array_push($block_['parentBlock'],$rendered['blockIds'][$prev]);
                }
            }
            $block_['blockId'] = $rendered['blockIds'][$block];
            $operand_= array();
            foreach ($ops as $op) {
                $operand=$op['label'];
                if ($attributes = $op['attributes']){
                    $operand['startLine'] = $attributes['startLine'];
                    $operand['endLine'] = $attributes['endLine'];
                    $operand['file'] = $attributes['filename'];
                } else {
                    $operand['file'] = "None";
                    $operand['startLine'] = "None";
                    $operand['endLine'] = "None";
                }
                foreach ($op['childBlocks'] as $child) {
                    if (array_key_exists($child['name'], $operand)) {
                        if (!is_array($operand[$child['name']])) {
                            $operand[$child['name']] = array($operand[$child['name']]);
                        }
                        array_push($operand[$child['name']], $rendered['blockIds'][$child['block']]);
                    } else {
                        $value = $rendered['blockIds'][$child['block']];
                        if (is_array($op['op']->{$child['name']})) {
                            $value = array($value);
                        }
                        $operand[$child['name']] = $value;
                    }
                }
                array_push($operand_,$operand);
            }
            $block_['blocks'] = $operand_;
            array_push($blocks,$block_);
        }
        return $blocks;
    }

    function printVars(\PHPCfg\Func $blocks) {

    }
}
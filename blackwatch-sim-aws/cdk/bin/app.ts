#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { BwsimStack } from "../lib/bwsim-stack";

const app = new cdk.App();
new BwsimStack(app, "BwsimStack");

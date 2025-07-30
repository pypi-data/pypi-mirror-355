r'''
# CDK Express Pipeline

[![npm version](https://badge.fury.io/js/cdk-express-pipeline.svg)](https://badge.fury.io/js/cdk-express-pipeline)
[![PyPI version](https://badge.fury.io/py/cdk-express-pipeline.svg)](https://badge.fury.io/py/cdk-express-pipeline)

<!-- TOC -->

* [Introduction](#introduction)
* [How does it work?](#how-does-it-work)
* [Deployment Order](#deployment-order)
* [Installation](#installation)
* [Usage](#usage)
* [Options](#options)
* [Selective Deployment](#selective-deployment)
* [Builds System Templates/Examples](#builds-system-templatesexamples)
* [Legacy Usage](#legacy-usage)
* [Demo Projects](#demo-projects)
* [Docs](#docs)

<!-- TOC -->

## Introduction

CDK Express Pipelines is a library that allows you to define your pipelines in CDK native method. It is built on
top of the [AWS CDK](https://aws.amazon.com/cdk/) and is an alternative
to [AWS CDK Pipelines](https://aws.amazon.com/cdk/pipelines/)
that is build system agnostic.

Features:

* Works on any system for example your local machine, GitHub, GitLab, etc.
* Uses the `cdk deploy` command to deploy your stacks
* It's fast. Make use of concurrent/parallel Stack deployments
* Stages and Waves are plain classes, not constructs, they do not change nested Construct IDs (like CDK Pipelines)
* Supports TS and Python CDK

Resources:

* [CDK Express Pipeline Tutorial](https://rehanvdm.com/blog/cdk-express-pipeline-tutorial)
* [Migrate from CDK Pipelines to CDK Express Pipeline](https://rehanvdm.com/blog/migrate-from-cdk-pipelines-to-cdk-express-pipeline)
* [Exploring CI/CD with AWS CDK Express Pipeline: Faster and Efficient Deployments](https://www.youtube.com/watch?v=pma4zP7mhMU)
  (YouTube channel [CI and CD on Amazon Web Services (AWS)](https://www.youtube.com/watch?v=pma4zP7mhMU))

## How does it work?

This library makes use of the fact that the CDK CLI computes the dependency graph of your stacks and deploys them in
the correct order. It creates the correct dependency graph between Waves, Stages and Stacks with the help of the
native `.addDependency` method of the CDK Stack. The `cdk deploy '**'` command will deploy all stacks in the correct
order.

## Deployment Order

The Wave, Stage and Stack order is as follows:

* Waves are deployed sequentially, one after the other.
* Stages within a Wave are deployed in parallel by default, unless configured to be sequential.
* Stacks within a Stage are deployed in order of stack dependencies within a Stage.

For example, the following definition of Waves, Stages and Stacks as in CDK Express Pipelines:

![order.png](https://github.com/rehanvdm/cdk-express-pipeline/blob/main/docs/_imgs/order.png)

Will create a dependency graph as follows:

![img.png](https://github.com/rehanvdm/cdk-express-pipeline/blob/main/docs/_imgs/order_dependencies.png)

When used with `cdk deploy '**' --concurrency 10`, it will deploy all stacks in parallel, 10 at a time, where possible
while still adhering to the dependency graph. Stacks will be deployed in the following order:

<details>
<summary>✨ Deployment order visualized ✨</summary>

![order_1.png](https://github.com/rehanvdm/cdk-express-pipeline/blob/main/docs/_imgs/order_1.png)

![order_2.png](https://github.com/rehanvdm/cdk-express-pipeline/blob/main/docs/_imgs/order_2.png)

![order_3.png](https://github.com/rehanvdm/cdk-express-pipeline/blob/main/docs/_imgs/order_3.png)

![order_4.png](https://github.com/rehanvdm/cdk-express-pipeline/blob/main/docs/_imgs/order_4.png)

![order_5.png](https://github.com/rehanvdm/cdk-express-pipeline/blob/main/docs/_imgs/order_5.png)

</details>

## Installation

### TS

```bash
npm install cdk-express-pipeline
```

Then import the library in your code:

```python
import { CdkExpressPipeline } from 'cdk-express-pipeline';
```

### Python

```bash
pip install cdk-express-pipeline
```

Then import the library in your code:

```python
from cdk_express_pipelines import CdkExpressPipeline
```

## Usage

The `ExpressStack` extends the `cdk.Stack` class and has a very similar signature, only taking an extra `stage`
parameter. There are multiple ways to build your pipeline, it involves creating the Pipeline, adding Waves, Stages and
Stacks to your Stages and then calling `.synth()` on the Pipeline. See the alternative expand sections for other
methods.

**Stack Definition:**

```python
  class StackA extends ExpressStack {
  constructor(scope: Construct, id: string, stage: ExpressStage, stackProps?: StackProps) {
    super(scope, id, stage, stackProps);

    new cdk.aws_sns.Topic(this, 'MyTopic');
    // ... more resources
  }
}

class StackB extends ExpressStack {
  //... similar to StackA
}

class StackC extends ExpressStack {
  //... similar to StackA
}
```

**1️⃣ Pipeline Definition:**

```python
const app = new App();
const expressPipeline = new CdkExpressPipeline();

// === Wave 1 ===
const wave1 = expressPipeline.addWave('Wave1');
// --- Wave 1, Stage 1---
const wave1Stage1 = wave1.addStage('Stage1');

const stackA = new StackA(app, 'StackA', wave1Stage1);
const stackB = new StackB(app, 'StackB', wave1Stage1);
stackB.addExpressDependency(stackA);

// === Wave 2 ===
const wave2 = expressPipeline.addWave('Wave2');
// --- Wave 2, Stage 1---
const wave2Stage1 = wave2.addStage('Stage1');
new StackC(app, 'StackC', wave2Stage1);
expressPipeline.synth([
  wave1,
  wave2,
]);
```

The stack deployment order will be printed to the console when running `cdk` commands:

```plaintext
ORDER OF DEPLOYMENT
🌊 Waves  - Deployed sequentially.
🏗️ Stages - Deployed in parallel by default, unless the wave is marked `[Seq 🏗️]` for sequential stage execution.
📦 Stacks - Deployed after their dependent stacks within the stage (dependencies shown below them with ↳).
           - Lines prefixed with a pipe (|) indicate stacks matching the CDK pattern.

🌊 Wave1
  🏗️ Stage1
    📦 StackA (Wave1_Stage1_StackA)
    📦 StackB (Wave1_Stage1_StackB)
        ↳ StackA
🌊 Wave2
  🏗️ Stage1
    📦 StackC (Wave2_Stage1_StackC)

```

<br><details>
<summary><b>2️⃣ Pipeline Definition Alternative - Stacks Nested in Stages:</b></summary>

```python
const app = new App();

class Wave1 extends ExpressWave {
  constructor() {
    super('Wave1');
  }
}

class Wave1Stage1 extends ExpressStage {
  constructor(wave1: Wave1) {
    super('Stage1', wave1);

    const stackA = new StackA(app, 'StackA', this);
    const stackB = new StackB(app, 'StackB', this);
    stackB.addExpressDependency(stackA);
  }
}

class Wave2 extends ExpressWave {
  constructor() {
    super('Wave2');
  }
}

class Wave2Stage1 extends ExpressStage {
  constructor(wave2: Wave2) {
    super('Stage1', wave2);

    new StackC(app, 'StackC', this);
  }
}

const expressPipeline = new CdkExpressPipeline();
const wave1 = new Wave1();
new Wave1Stage1(wave1);
const wave2 = new Wave2();
new Wave2Stage1(wave2);
expressPipeline.synth([wave1, wave2]);
```

</details><br><details>
<summary><b>3️⃣ Pipeline Definition Alternative - Extending all without nesting:</b></summary>

```python
const app = new App();

// --- Custom Wave Class ---
class MyExpressWave extends ExpressWave {
  constructor(props: ExpressWaveProps) {
    super('My' + props.id);
  }
}

// --- Custom Stage Class ---
class MyExpressStage extends ExpressStage {
  constructor(id: string, wave: MyExpressWave, stacks?: MyExpressStack[]) {
    super('My' + id, wave, stacks);
  }
}

// --- Custom Stack Class ---
class MyExpressStack extends ExpressStack {
  constructor(scope: Construct, id: string, stage: MyExpressStage, stackProps?: StackProps) {
    super(scope, 'My' + id, stage, stackProps);
  }
}

const expressPipeline = new CdkExpressPipeline();
const wave1 = new MyExpressWave({ id: 'Wave1' });
const wave1Stage1 = new MyExpressStage('Stage1', wave1);
const stackA = new MyExpressStack(app, 'StackA', wave1Stage1);
expressPipeline.synth([wave1]);

expect(stackA.id).toBe('MyWave1_MyStage1_MyStackA');
```

</details>

## Options

### Separator

By default, the library uses an underscore (`_`) as the separator between Wave, Stage and Stack IDs. Not available in
the Legacy classes. This can be customized by passing a different separator to the `CdkExpressPipeline` constructor:

```python
const expressPipeline = new CdkExpressPipeline({
  separator: '-', // Now stack IDs will be like: Wave1-Stage1-StackA
});
```

### Sequential Stages

By default, stages within a wave are deployed in parallel. You can configure a wave to deploy its stages sequentially
by setting the `sequentialStages` option:

```python
const wave1 = expressPipeline.addWave('Wave1', {
  sequentialStages: true, // Stages in this wave will be deployed one after another
});
```

When stages are configured to be sequential, they will be marked with `[Seq 🏗️]` in the deployment order output:

```plaintext
🌊 Wave1 [Seq 🏗️]
  🏗️ Stage1
    📦 StackA (Wave1_Stage1_StackA)
  🏗️ Stage2
    📦 StackB (Wave1_Stage2_StackB)
```

## Selective Deployment

Leverages a consistent and predictable naming convention for Stack IDs. A Stack ID consists of the Wave, Stage and
original Stack ID. This enables us to target Waves, Stages or individual stacks for deployment. For example, given the
following stack IDs:

```
Wave1_Stage1_StackA
Wave1_Stage1_StackB
Wave1_Stage1_StackC
Wave1_Stage2_StackD

Wave2_Stage1_StackE
Wave2_Stage1_StackF
```

It makes targeted deployments easy:

* Deploy Wave1: `cdk deploy 'Wave1_*'` deploys all stacks in `Wave1`
* Deploy Wave1 Stage1: `cdk deploy 'Wave1_Stage1_*'` deploys all stacks in `Wave1_Stage1`
* Deploy Wave1 Stage1 StackA: `cdk deploy 'Wave1_Stage1_StackA'` deploys only `Wave1_Stage1_StackA`

> [!IMPORTANT]
> When targeting specific stacks be sure to pass the `--exclusively` flag to the `cdk deploy` command to only deploy
> the specified stacks and not its dependencies.

Benefits of selecting a specific Wave, Stage or Stack over the all `'**'` method:

* While developing, you can speed up deployments from your local machine by deploying only what you are working on.
* When deploying with a CI/CD system, you can have additional logic between them. For example, you can place a
  manual approval step between `Wave1` and `Wave2`.

## Builds System Templates/Examples

### Local

These examples all assume a project created with the default structure of the CDK CLI
command `cdk init app --language typescript`.

These example are taken from the demo TS project: https://github.com/rehanvdm/cdk-express-pipeline-demo-ts

**Diff commands**

```bash
# Diffs all stacks
cdk diff '**' --profile YOUR_PROFILE
# Diffs only specific stacks in a Wave
cdk diff 'Wave1_*' --profile YOUR_PROFILE --exclusively
# Diffs only specific stacks of a Stage in a Wave
cdk diff 'Wave1_Stage1_*' --profile YOUR_PROFILE --exclusively
# Diffs only a specific stack
cdk diff 'Wave1_Stage1_StackA' --profile YOUR_PROFILE --exclusively
```

**Deploy commands**

```bash
# Deploys all stacks in correct order
cdk deploy '**' --profile YOUR_PROFILE --concurrency 10 --require-approval never
# Deploys only specific stacks in a Wave in correct order
cdk deploy 'Wave1_*' --profile YOUR_PROFILE --exclusively --concurrency 10 --require-approval never
# Deploys only specific stacks of a Stage in a Wave in correct order
cdk deploy 'Wave1_Stage1_*' --profile YOUR_PROFILE --exclusively --concurrency 10 --require-approval never
# Deploys only a specific stack
cdk deploy 'Wave1_Stage1_StackA' --profile YOUR_PROFILE --exclusively --concurrency 10 --require-approval never
```

### GitHub Workflows

These examples all assume a project created with the default structure of the CDK CLI
command `cdk init app --language typescript`.

These example are taken from the demo TS project: https://github.com/rehanvdm/cdk-express-pipeline-demo-ts

<details>
<summary>.github/workflows/diff.yml</summary>

Does a build and CDK Diff on PR open and push, the `cdk diff` output can be viewed in the action run logs.

```yaml
name: Diff
on:
  pull_request:
    types: [ opened, synchronize ]
  workflow_dispatch: { }

env:
  FORCE_COLOR: 1

jobs:
  deploy:
    name: CDK Diff and Deploy
    runs-on: ubuntu-latest
    permissions:
      actions: write
      contents: read
      id-token: write
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up node
        uses: actions/setup-node@v3
        with:
          node-version: 20
          cache: npm

      - name: Install dependencies
        run: npm install ci

      # TODO: Alternatively use an AWS IAM user and set the credentials in GitHub Secrets (less secure than GH OIDC below)
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: # TODO: Your role to assume
          aws-region: # TODO: your region

      - name: CDK diff
        run: npm run cdk -- diff '**'
```

Produces the following output in the GitHub Action logs:

![diff.png](https://github.com/rehanvdm/cdk-express-pipeline/blob/main/docs/_imgs/action_logs/diff.png)

</details><details>
<summary>.github/workflows/deploy.yml</summary>

Does a build, CDK Diff and Deploy when a push happens on the `main` branch.

```yaml
name: Deploy
on:
  push:
    branches:
      - main

env:
  FORCE_COLOR: 1

jobs:
  deploy:
    name: CDK Diff and Deploy
    runs-on: ubuntu-latest
    permissions:
      actions: write
      contents: read
      id-token: write
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up node
        uses: actions/setup-node@v3
        with:
          node-version: 20
          cache: npm

      - name: Install dependencies
        run: npm install ci

      # TODO: Alternatively use an AWS IAM user and set the credentials in GitHub Secrets (less secure than GH OIDC below)
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: # TODO: Your role to assume
          aws-region: # TODO: your region

      - name: CDK diff
        run: npm run cdk -- diff '**'

      - name: CDK deploy
        run: npm run cdk -- deploy '**' --require-approval never --concurrency 10
```

Produces the following output in the GitHub Action logs:

![diff.png](https://github.com/rehanvdm/cdk-express-pipeline/blob/main/docs/_imgs/action_logs/deploy.png)

</details><details>
<summary>.github/workflows/deploy-advance.yml</summary>

The `synth` job builds the CDK app and saves the cloud assembly to the `./cloud_assembly_output` directory. The whole
repo with installed NPM packages and the cloud assembly is then cached. This job of the pipeline does not have access
to any AWS Secrets, the installing of packages and building is decoupled from the deployment improving security.

The `wave1` and `wave2` jobs fetches the cloud assembly from the cache and then does a CDK Diff and Deploy on only their
stacks. The `wave1` job targets all the stacks that start with `Wave1_` and the `wave2` job targets all the stacks that
start with `Wave2_`. It is important to add the `--exclusively` flag to only focus on the specified stacks and not its
dependencies.

```yaml
name: Deploy Advance
on:
  push:
    branches:
      - main
  workflow_dispatch: { } # While testing only

env:
  FORCE_COLOR: 1

jobs:
  synth:
    name: Build and CDK Synth
    runs-on: ubuntu-latest
    permissions:
      actions: write

      contents: read
      id-token: write
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up node
        uses: actions/setup-node@v3
        with:
          node-version: 20
          cache: npm

      - name: Install dependencies
        run: npm install ci

      - name: CDK Synth
        run: npm run cdk -- synth --output ./cloud_assembly_output

      - name: Cache CDK Assets
        uses: actions/cache/save@v4
        with:
          path: ./
          key: "cdk-assets-${{ github.sha }}"

  wave1:
    name: Wave 1
    needs:
      - synth
    runs-on: ubuntu-latest
    permissions:
      actions: write
      contents: read
      id-token: write
    steps:
      - name: Fetch CDK Assets
        uses: actions/cache/restore@v4
        with:
          path: ./
          key: "cdk-assets-${{ github.sha }}"

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::581184285249:role/githuboidc-git-hub-deploy-role
          aws-region: eu-west-1

      - name: CDK diff
        run: npm run cdk -- diff 'Wave1_*' --exclusively --app ./cloud_assembly_output

      - name: CDK deploy
        run: npm run cdk -- deploy 'Wave1_*' --require-approval never --concurrency 10 --exclusively --app ./cloud_assembly_output

  # Manual approval

  wave2:
    name: Wave 2
    needs:
      - wave1
    runs-on: ubuntu-latest
    permissions:
      actions: write
      contents: read
      id-token: write
    steps:
      - name: Fetch CDK Assets
        uses: actions/cache/restore@v4
        with:
          path: ./
          key: "cdk-assets-${{ github.sha }}"

      # TODO: Alternatively use an AWS IAM user and set the credentials in GitHub Secrets (less secure than GH OIDC below)
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: # TODO: Your role to assume
          aws-region: # TODO: your region

      - name: CDK diff
        run: npm run cdk -- diff 'Wave2_*' --exclusively --app ./cloud_assembly_output

      - name: CDK deploy
        run: npm run cdk -- deploy 'Wave2_*' --require-approval never --concurrency 10 --exclusively --app ./cloud_assembly_output
```

Produces the following output in the GitHub Action logs:

![deploy_adv.png](https://github.com/rehanvdm/cdk-express-pipeline/blob/main/docs/_imgs/action_logs/deploy_adv.png)

![deploy_adv_1.png](https://github.com/rehanvdm/cdk-express-pipeline/blob/main/docs/_imgs/action_logs/deploy_adv_1.png)

</details>

### GitLab

TODO...

### Any other build system

...

## Legacy Usage

The `CdkExpressPipelineLegacy` class can be used when you do not want/can not use the `ExpressStack` class and have to
stick to the CDK `Stack` class.

> [!WARNING]
> Always use non-legacy classes for greenfield projects. Only use the Legacy classes if you have no other choice.

The following features are not available when using the Legacy classes:

* Enforcing Wave, Stage and Stack names do not include the `separator` character.
* Enforcing that a Stack in Stage 1 can not depend on a Stack in Stage 2.
* Printing stack dependencies within a Stage. Since we do not know what stage a stack belongs to, it's not possible to
  print the dependencies of stacks of only that stage and not others.
* If a consistent naming convention has not been followed for Stacks, it might not be possible to target all stacks in a
  stage or a wave. Deployment will have to always target all stacks with `"**"`.
* Stack ids are not changed and have to be unique across all stacks in the CDK app, whereas with the non-legacy
  classes, stack ids only have to be unique within a Wave.

**Stack Definition:**

```python
class StackA extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    new cdk.aws_sns.Topic(this, 'MyTopicA');
    // ... more resources
  }
}

class StackB extends cdk.Stack {
  // ... similar to StackA
}

class StackC extends cdk.Stack {

}
```

**1️⃣ Pipeline Definition:**

```python
const app = new App();
const expressPipeline = new CdkExpressPipelineLegacy();

/* === Wave 1 === */
/* --- Wave 1, Stage 1--- */
const stackA = new StackA(app, 'StackA');
const stackB = new StackB(app, 'StackB');
stackB.addDependency(stackA);

// === Wave 2 ===
/* --- Wave 2, Stage 1--- */
const stackC = new StackC(app, 'StackC');

expressPipeline.synth([
  {
    id: 'Wave1',
    stages: [{
      id: 'Stage1',
      stacks: [
        stackA,
        stackB,
      ],
    }],
  },
  {
    id: 'Wave2',
    stages: [{
      id: 'Stage1',
      stacks: [
        stackC,
      ],
    }],
  },
]);
```

The stack deployment order will be printed to the console when running `cdk` commands:

```plaintext
ORDER OF DEPLOYMENT
🌊 Waves  - Deployed sequentially.
🏗️ Stages - Deployed in parallel by default, unless the wave is marked `[Seq 🏗️]` for sequential stage execution.
📦 Stacks - Deployed after their dependent stacks within the stage (dependencies shown below them with ↳).
           - Lines prefixed with a pipe (|) indicate stacks matching the CDK pattern.

🌊 Wave1
  🏗️ Stage1
    📦 StackA
    📦 StackB
🌊 Wave2
  🏗️ Stage1
    📦 StackC
```

<details>
<summary><b>2️⃣ Pipeline Definition Alternative - method builder:</b></summary>

```python
const app = new App();
const expressPipeline = new CdkExpressPipelineLegacy();

/* === Wave 1 === */
const wave1 = expressPipeline.addWave('Wave1');
/* --- Wave 1, Stage 1--- */
const wave1Stage1 = wave1.addStage('Stage1');
const stackA = wave1Stage1.addStack(new StackA(app, 'StackA'));
const stackB = wave1Stage1.addStack(new StackB(app, 'StackB'));
stackB.addDependency(stackA);

// === Wave 2 ===
const wave2 = expressPipeline.addWave('Wave2');
/* --- Wave 2, Stage 1--- */
const wave2Stage1 = wave2.addStage('Stage1');
wave2Stage1.addStack(new StackC(app, 'StackC'));

expressPipeline.synth([
  wave1,
  wave2,
]);
```

</details>

## Demo Projects

* [CDK Express Pipeline Demo TS](https://github.com/rehanvdm/cdk-express-pipeline-demo-ts)
* [CDK Express Pipeline Demo Python](https://github.com/rehanvdm/cdk-express-pipeline-demo-python)

## Docs

* [FAQ](https://github.com/rehanvdm/cdk-express-pipeline/blob/main/docs/FAQ.md)
* [Projen Sacrifices](https://github.com/rehanvdm/cdk-express-pipeline/blob/main/docs/Projen%20Sacrifices.md)
* [API](https://github.com/rehanvdm/cdk-express-pipeline/blob/main/API.md)
'''
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from ._jsii import *

import aws_cdk as _aws_cdk_ceddda9d
import constructs as _constructs_77d1e7e8


class CdkExpressPipeline(
    metaclass=jsii.JSIIMeta,
    jsii_type="cdk-express-pipeline.CdkExpressPipeline",
):
    '''A CDK Express Pipeline that defines the order in which the stacks are deployed.'''

    def __init__(
        self,
        *,
        separator: typing.Optional[builtins.str] = None,
        waves: typing.Optional[typing.Sequence["ExpressWave"]] = None,
    ) -> None:
        '''
        :param separator: Separator between the wave, stage and stack ids that are concatenated to form the stack id. Default: _
        :param waves: The waves in the pipeline.
        '''
        props = CdkExpressPipelineProps(separator=separator, waves=waves)

        jsii.create(self.__class__, self, [props])

    @jsii.member(jsii_name="addWave")
    def add_wave(
        self,
        id: builtins.str,
        sequential_stages: typing.Optional[builtins.bool] = None,
    ) -> "IExpressWave":
        '''Add a wave to the pipeline.

        :param id: The wave identifier.
        :param sequential_stages: If true, the stages in the wave will be executed sequentially. Default: false.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__51d5a812c29abca46e9446db3e0acfaedb3fb0f70a5ccbc26b8b26b62c731b30)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument sequential_stages", value=sequential_stages, expected_type=type_hints["sequential_stages"])
        return typing.cast("IExpressWave", jsii.invoke(self, "addWave", [id, sequential_stages]))

    @jsii.member(jsii_name="printWaves")
    def print_waves(self, waves: typing.Sequence["IExpressWave"]) -> None:
        '''Print the order of deployment to the console.

        :param waves: -

        :private: true
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e18d77fb9496cb5fdeabb0fe5a14c3dcd08b7a4747694ac0a799b01dfa105a34)
            check_type(argname="argument waves", value=waves, expected_type=type_hints["waves"])
        return typing.cast(None, jsii.invoke(self, "printWaves", [waves]))

    @jsii.member(jsii_name="synth")
    def synth(
        self,
        waves: typing.Optional[typing.Sequence["IExpressWave"]] = None,
        print: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Synthesize the pipeline which creates the dependencies between the stacks in the correct order.

        :param waves: The waves to synthesize.
        :param print: Whether to print the order of deployment to the console.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ddf3f54429b9cebdd63080df8e42a8f0bee80ea5889f7848d8110f99befcf433)
            check_type(argname="argument waves", value=waves, expected_type=type_hints["waves"])
            check_type(argname="argument print", value=print, expected_type=type_hints["print"])
        return typing.cast(None, jsii.invoke(self, "synth", [waves, print]))

    @builtins.property
    @jsii.member(jsii_name="waves")
    def waves(self) -> typing.List["IExpressWave"]:
        return typing.cast(typing.List["IExpressWave"], jsii.get(self, "waves"))


class CdkExpressPipelineLegacy(
    metaclass=jsii.JSIIMeta,
    jsii_type="cdk-express-pipeline.CdkExpressPipelineLegacy",
):
    '''A CDK Express Pipeline that defines the order in which the stacks are deployed.

    This is the legacy version of the pipeline that uses the ``Stack`` class, for plug and play compatibility with existing CDK projects that can not
    use the ``ExpressStack`` class. For new projects, use the ``CdkExpressPipeline`` class.
    '''

    def __init__(
        self,
        waves: typing.Optional[typing.Sequence["IExpressWaveLegacy"]] = None,
    ) -> None:
        '''
        :param waves: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5e78d8fa8554a29ac59173413b98062741ae83aeb4754f02a80c85c27e16d8ce)
            check_type(argname="argument waves", value=waves, expected_type=type_hints["waves"])
        jsii.create(self.__class__, self, [waves])

    @jsii.member(jsii_name="addWave")
    def add_wave(
        self,
        id: builtins.str,
        sequential_stages: typing.Optional[builtins.bool] = None,
    ) -> "ExpressWaveLegacy":
        '''Add a wave to the pipeline.

        :param id: The wave identifier.
        :param sequential_stages: If true, the stages in the wave will be executed sequentially. Default: false.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__58733341409ff8a6c60fbf06de891a31f81f41cf55e7503aaa0238ee46ff5166)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument sequential_stages", value=sequential_stages, expected_type=type_hints["sequential_stages"])
        return typing.cast("ExpressWaveLegacy", jsii.invoke(self, "addWave", [id, sequential_stages]))

    @jsii.member(jsii_name="printWaves")
    def print_waves(self, waves: typing.Sequence["IExpressWaveLegacy"]) -> None:
        '''Print the order of deployment to the console.

        :param waves: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6d22fe922729d650ca61abf0f4568bb8cbafe791434481f3e0cce74d098f785e)
            check_type(argname="argument waves", value=waves, expected_type=type_hints["waves"])
        return typing.cast(None, jsii.invoke(self, "printWaves", [waves]))

    @jsii.member(jsii_name="synth")
    def synth(
        self,
        waves: typing.Optional[typing.Sequence["IExpressWaveLegacy"]] = None,
        print: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Synthesize the pipeline which creates the dependencies between the stacks in the correct order.

        :param waves: The waves to synthesize.
        :param print: Whether to print the order of deployment to the console.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0c7d8bd5a65c1437ed17046edfb50f14e1f2b8f73c9db08927132a10f37d409d)
            check_type(argname="argument waves", value=waves, expected_type=type_hints["waves"])
            check_type(argname="argument print", value=print, expected_type=type_hints["print"])
        return typing.cast(None, jsii.invoke(self, "synth", [waves, print]))

    @builtins.property
    @jsii.member(jsii_name="waves")
    def waves(self) -> typing.List["IExpressWaveLegacy"]:
        return typing.cast(typing.List["IExpressWaveLegacy"], jsii.get(self, "waves"))

    @waves.setter
    def waves(self, value: typing.List["IExpressWaveLegacy"]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__54082bd27a8ceffd74f1b6a0cb05b3bbcf4ffa9ada94c72e52e645687ad4ad5b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "waves", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="cdk-express-pipeline.CdkExpressPipelineProps",
    jsii_struct_bases=[],
    name_mapping={"separator": "separator", "waves": "waves"},
)
class CdkExpressPipelineProps:
    def __init__(
        self,
        *,
        separator: typing.Optional[builtins.str] = None,
        waves: typing.Optional[typing.Sequence["ExpressWave"]] = None,
    ) -> None:
        '''
        :param separator: Separator between the wave, stage and stack ids that are concatenated to form the stack id. Default: _
        :param waves: The waves in the pipeline.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cc99a79d5da23f439f19b4717a315983fa455ec2ae7d0300ac3d7381d5892205)
            check_type(argname="argument separator", value=separator, expected_type=type_hints["separator"])
            check_type(argname="argument waves", value=waves, expected_type=type_hints["waves"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if separator is not None:
            self._values["separator"] = separator
        if waves is not None:
            self._values["waves"] = waves

    @builtins.property
    def separator(self) -> typing.Optional[builtins.str]:
        '''Separator between the wave, stage and stack ids that are concatenated to form the stack id.

        :default: _
        '''
        result = self._values.get("separator")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def waves(self) -> typing.Optional[typing.List["ExpressWave"]]:
        '''The waves in the pipeline.'''
        result = self._values.get("waves")
        return typing.cast(typing.Optional[typing.List["ExpressWave"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CdkExpressPipelineProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="cdk-express-pipeline.ExpressWaveProps",
    jsii_struct_bases=[],
    name_mapping={"id": "id", "separator": "separator"},
)
class ExpressWaveProps:
    def __init__(
        self,
        *,
        id: builtins.str,
        separator: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param id: 
        :param separator: Separator between the wave, stage and stack ids that are concatenated to form the stack id. Default: ``_``
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d91dc79595e990d6da1a185afde4e65465da1f5dc12abd5220e16803db5481a2)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument separator", value=separator, expected_type=type_hints["separator"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }
        if separator is not None:
            self._values["separator"] = separator

    @builtins.property
    def id(self) -> builtins.str:
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def separator(self) -> typing.Optional[builtins.str]:
        '''Separator between the wave, stage and stack ids that are concatenated to form the stack id.

        :default: ``_``
        '''
        result = self._values.get("separator")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ExpressWaveProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.interface(jsii_type="cdk-express-pipeline.IExpressStack")
class IExpressStack(typing_extensions.Protocol):
    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The stack identifier which is a combination of the wave, stage and stack id.'''
        ...

    @id.setter
    def id(self, value: builtins.str) -> None:
        ...

    @builtins.property
    @jsii.member(jsii_name="stage")
    def stage(self) -> "ExpressStage":
        '''The stage that the stack belongs to.'''
        ...

    @stage.setter
    def stage(self, value: "ExpressStage") -> None:
        ...

    @jsii.member(jsii_name="addExpressDependency")
    def add_express_dependency(
        self,
        target: "ExpressStack",
        reason: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Add a dependency between this stack and another ExpressStack.

        This can be used to define dependencies between any two stacks within an

        :param target: The ``ExpressStack`` to depend on.
        :param reason: The reason for the dependency.
        '''
        ...

    @jsii.member(jsii_name="expressDependencies")
    def express_dependencies(self) -> typing.List["ExpressStack"]:
        '''The ExpressStack dependencies of the stack.'''
        ...


class _IExpressStackProxy:
    __jsii_type__: typing.ClassVar[str] = "cdk-express-pipeline.IExpressStack"

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The stack identifier which is a combination of the wave, stage and stack id.'''
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__76bd73c874b49b4683b044d917cc6800ed471f2b41d3164b902c206407432cbe)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="stage")
    def stage(self) -> "ExpressStage":
        '''The stage that the stack belongs to.'''
        return typing.cast("ExpressStage", jsii.get(self, "stage"))

    @stage.setter
    def stage(self, value: "ExpressStage") -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__61a812768afc62205a9db0f1f9d01095658800d0cc43087913d4c1645cde7bdd)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "stage", value) # pyright: ignore[reportArgumentType]

    @jsii.member(jsii_name="addExpressDependency")
    def add_express_dependency(
        self,
        target: "ExpressStack",
        reason: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Add a dependency between this stack and another ExpressStack.

        This can be used to define dependencies between any two stacks within an

        :param target: The ``ExpressStack`` to depend on.
        :param reason: The reason for the dependency.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0a14719acbf68f0fd518f950b2dd5d2922f8e4c9c9273c2f85d05589af97f191)
            check_type(argname="argument target", value=target, expected_type=type_hints["target"])
            check_type(argname="argument reason", value=reason, expected_type=type_hints["reason"])
        return typing.cast(None, jsii.invoke(self, "addExpressDependency", [target, reason]))

    @jsii.member(jsii_name="expressDependencies")
    def express_dependencies(self) -> typing.List["ExpressStack"]:
        '''The ExpressStack dependencies of the stack.'''
        return typing.cast(typing.List["ExpressStack"], jsii.invoke(self, "expressDependencies", []))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IExpressStack).__jsii_proxy_class__ = lambda : _IExpressStackProxy


@jsii.interface(jsii_type="cdk-express-pipeline.IExpressStage")
class IExpressStage(typing_extensions.Protocol):
    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The stage identifier.'''
        ...

    @id.setter
    def id(self, value: builtins.str) -> None:
        ...

    @builtins.property
    @jsii.member(jsii_name="stacks")
    def stacks(self) -> typing.List["ExpressStack"]:
        '''The stacks in the stage.'''
        ...

    @stacks.setter
    def stacks(self, value: typing.List["ExpressStack"]) -> None:
        ...

    @builtins.property
    @jsii.member(jsii_name="wave")
    def wave(self) -> "ExpressWave":
        '''The wave that the stage belongs to.'''
        ...

    @wave.setter
    def wave(self, value: "ExpressWave") -> None:
        ...


class _IExpressStageProxy:
    __jsii_type__: typing.ClassVar[str] = "cdk-express-pipeline.IExpressStage"

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The stage identifier.'''
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fbca333d17cf67f3ebc52a25d3e08fdc38766f46ae2bcaeff4c01e2edbbd5dce)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="stacks")
    def stacks(self) -> typing.List["ExpressStack"]:
        '''The stacks in the stage.'''
        return typing.cast(typing.List["ExpressStack"], jsii.get(self, "stacks"))

    @stacks.setter
    def stacks(self, value: typing.List["ExpressStack"]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d28e54cfe0e98d05cd17fa7ea13e156a82d091df55640c4094698ec7e78ed884)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "stacks", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="wave")
    def wave(self) -> "ExpressWave":
        '''The wave that the stage belongs to.'''
        return typing.cast("ExpressWave", jsii.get(self, "wave"))

    @wave.setter
    def wave(self, value: "ExpressWave") -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ce620906fddfafba1ff8377098c5f9c35ada5694e2e5c6f9d15368e7d1d4c517)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wave", value) # pyright: ignore[reportArgumentType]

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IExpressStage).__jsii_proxy_class__ = lambda : _IExpressStageProxy


@jsii.interface(jsii_type="cdk-express-pipeline.IExpressStageLegacy")
class IExpressStageLegacy(typing_extensions.Protocol):
    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The stage identifier.'''
        ...

    @id.setter
    def id(self, value: builtins.str) -> None:
        ...

    @builtins.property
    @jsii.member(jsii_name="stacks")
    def stacks(self) -> typing.List[_aws_cdk_ceddda9d.Stack]:
        '''The stacks in the stage.'''
        ...

    @stacks.setter
    def stacks(self, value: typing.List[_aws_cdk_ceddda9d.Stack]) -> None:
        ...


class _IExpressStageLegacyProxy:
    __jsii_type__: typing.ClassVar[str] = "cdk-express-pipeline.IExpressStageLegacy"

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The stage identifier.'''
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2fdf2493af932e5d33d989d572f161b8c998d0298e6a848f0a7af5edeca7b052)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="stacks")
    def stacks(self) -> typing.List[_aws_cdk_ceddda9d.Stack]:
        '''The stacks in the stage.'''
        return typing.cast(typing.List[_aws_cdk_ceddda9d.Stack], jsii.get(self, "stacks"))

    @stacks.setter
    def stacks(self, value: typing.List[_aws_cdk_ceddda9d.Stack]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fffd047542b1ad122d53335fcab6ee350d782b3038d2efbf3f05152a18e8559c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "stacks", value) # pyright: ignore[reportArgumentType]

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IExpressStageLegacy).__jsii_proxy_class__ = lambda : _IExpressStageLegacyProxy


@jsii.interface(jsii_type="cdk-express-pipeline.IExpressWave")
class IExpressWave(typing_extensions.Protocol):
    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The wave identifier.'''
        ...

    @id.setter
    def id(self, value: builtins.str) -> None:
        ...

    @builtins.property
    @jsii.member(jsii_name="separator")
    def separator(self) -> builtins.str:
        '''Separator between the wave, stage and stack ids that are concatenated to form the final stack id.'''
        ...

    @separator.setter
    def separator(self, value: builtins.str) -> None:
        ...

    @builtins.property
    @jsii.member(jsii_name="stages")
    def stages(self) -> typing.List["ExpressStage"]:
        '''The ExpressStages in the wave.'''
        ...

    @stages.setter
    def stages(self, value: typing.List["ExpressStage"]) -> None:
        ...

    @builtins.property
    @jsii.member(jsii_name="sequentialStages")
    def sequential_stages(self) -> typing.Optional[builtins.bool]:
        '''If true, the stages in the wave will be executed sequentially.

        :default: false
        '''
        ...

    @sequential_stages.setter
    def sequential_stages(self, value: typing.Optional[builtins.bool]) -> None:
        ...

    @jsii.member(jsii_name="addStage")
    def add_stage(self, id: builtins.str) -> "ExpressStage":
        '''Add an ExpressStage to the wave.

        :param id: The ExpressStage identifier.
        '''
        ...


class _IExpressWaveProxy:
    __jsii_type__: typing.ClassVar[str] = "cdk-express-pipeline.IExpressWave"

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The wave identifier.'''
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8030e0d36f67ca6d88248c3aebc00cb88a9491700acbd6c7d3e4f5f06dcff718)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="separator")
    def separator(self) -> builtins.str:
        '''Separator between the wave, stage and stack ids that are concatenated to form the final stack id.'''
        return typing.cast(builtins.str, jsii.get(self, "separator"))

    @separator.setter
    def separator(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2deeb751aa022d2277fc1af871b8a9419aaef6e789a22f82063f21230a6d03fa)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "separator", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="stages")
    def stages(self) -> typing.List["ExpressStage"]:
        '''The ExpressStages in the wave.'''
        return typing.cast(typing.List["ExpressStage"], jsii.get(self, "stages"))

    @stages.setter
    def stages(self, value: typing.List["ExpressStage"]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c33defa4497d6fd82c65487c1c51107af3c835ae4d7e1216f929dd314edaca26)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "stages", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sequentialStages")
    def sequential_stages(self) -> typing.Optional[builtins.bool]:
        '''If true, the stages in the wave will be executed sequentially.

        :default: false
        '''
        return typing.cast(typing.Optional[builtins.bool], jsii.get(self, "sequentialStages"))

    @sequential_stages.setter
    def sequential_stages(self, value: typing.Optional[builtins.bool]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ae1159ae328148533b46258d902359880ce2c3976c0b7e6fc201ec69c017e429)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sequentialStages", value) # pyright: ignore[reportArgumentType]

    @jsii.member(jsii_name="addStage")
    def add_stage(self, id: builtins.str) -> "ExpressStage":
        '''Add an ExpressStage to the wave.

        :param id: The ExpressStage identifier.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d0c0680f13cf234d76dc5ad77fd9b99005e303ff37a88d475016ab8e65495bbf)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        return typing.cast("ExpressStage", jsii.invoke(self, "addStage", [id]))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IExpressWave).__jsii_proxy_class__ = lambda : _IExpressWaveProxy


@jsii.interface(jsii_type="cdk-express-pipeline.IExpressWaveLegacy")
class IExpressWaveLegacy(typing_extensions.Protocol):
    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The wave identifier.'''
        ...

    @id.setter
    def id(self, value: builtins.str) -> None:
        ...

    @builtins.property
    @jsii.member(jsii_name="stages")
    def stages(self) -> typing.List[IExpressStageLegacy]:
        '''The ExpressStages in the wave.'''
        ...

    @stages.setter
    def stages(self, value: typing.List[IExpressStageLegacy]) -> None:
        ...

    @builtins.property
    @jsii.member(jsii_name="sequentialStages")
    def sequential_stages(self) -> typing.Optional[builtins.bool]:
        '''If true, the stages in the wave will be executed sequentially.

        :default: false
        '''
        ...

    @sequential_stages.setter
    def sequential_stages(self, value: typing.Optional[builtins.bool]) -> None:
        ...


class _IExpressWaveLegacyProxy:
    __jsii_type__: typing.ClassVar[str] = "cdk-express-pipeline.IExpressWaveLegacy"

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The wave identifier.'''
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ebcd93f3691046bc34c345a2d0c5fd123d149d6852a73f251c4a5caeef0b161a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="stages")
    def stages(self) -> typing.List[IExpressStageLegacy]:
        '''The ExpressStages in the wave.'''
        return typing.cast(typing.List[IExpressStageLegacy], jsii.get(self, "stages"))

    @stages.setter
    def stages(self, value: typing.List[IExpressStageLegacy]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c8bc3fea3bdc86a865ca6e2fcf12e74fb6190d42fb2b51e85f0be6ed539336b3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "stages", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sequentialStages")
    def sequential_stages(self) -> typing.Optional[builtins.bool]:
        '''If true, the stages in the wave will be executed sequentially.

        :default: false
        '''
        return typing.cast(typing.Optional[builtins.bool], jsii.get(self, "sequentialStages"))

    @sequential_stages.setter
    def sequential_stages(self, value: typing.Optional[builtins.bool]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__344bf89503483c6b8c5fcb2f9805b54198866f417be91cb3b67b3d568e301831)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sequentialStages", value) # pyright: ignore[reportArgumentType]

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IExpressWaveLegacy).__jsii_proxy_class__ = lambda : _IExpressWaveLegacyProxy


@jsii.implements(IExpressStack)
class ExpressStack(
    _aws_cdk_ceddda9d.Stack,
    metaclass=jsii.JSIIMeta,
    jsii_type="cdk-express-pipeline.ExpressStack",
):
    '''A CDK Express Pipeline Stack that belongs to an ExpressStage.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        stage: "ExpressStage",
        *,
        analytics_reporting: typing.Optional[builtins.bool] = None,
        cross_region_references: typing.Optional[builtins.bool] = None,
        description: typing.Optional[builtins.str] = None,
        env: typing.Optional[typing.Union[_aws_cdk_ceddda9d.Environment, typing.Dict[builtins.str, typing.Any]]] = None,
        permissions_boundary: typing.Optional[_aws_cdk_ceddda9d.PermissionsBoundary] = None,
        stack_name: typing.Optional[builtins.str] = None,
        suppress_template_indentation: typing.Optional[builtins.bool] = None,
        synthesizer: typing.Optional[_aws_cdk_ceddda9d.IStackSynthesizer] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        termination_protection: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Constructs a new instance of the ExpressStack class.

        :param scope: The parent of this stack, usually an ``App`` but could be any construct.
        :param id: The stack identifier which will be used to construct the final id as a combination of the wave, stage and stack id.
        :param stage: The stage that the stack belongs to.
        :param analytics_reporting: Include runtime versioning information in this Stack. Default: ``analyticsReporting`` setting of containing ``App``, or value of 'aws:cdk:version-reporting' context key
        :param cross_region_references: Enable this flag to allow native cross region stack references. Enabling this will create a CloudFormation custom resource in both the producing stack and consuming stack in order to perform the export/import This feature is currently experimental Default: false
        :param description: A description of the stack. Default: - No description.
        :param env: The AWS environment (account/region) where this stack will be deployed. Set the ``region``/``account`` fields of ``env`` to either a concrete value to select the indicated environment (recommended for production stacks), or to the values of environment variables ``CDK_DEFAULT_REGION``/``CDK_DEFAULT_ACCOUNT`` to let the target environment depend on the AWS credentials/configuration that the CDK CLI is executed under (recommended for development stacks). If the ``Stack`` is instantiated inside a ``Stage``, any undefined ``region``/``account`` fields from ``env`` will default to the same field on the encompassing ``Stage``, if configured there. If either ``region`` or ``account`` are not set nor inherited from ``Stage``, the Stack will be considered "*environment-agnostic*"". Environment-agnostic stacks can be deployed to any environment but may not be able to take advantage of all features of the CDK. For example, they will not be able to use environmental context lookups such as ``ec2.Vpc.fromLookup`` and will not automatically translate Service Principals to the right format based on the environment's AWS partition, and other such enhancements. Default: - The environment of the containing ``Stage`` if available, otherwise create the stack will be environment-agnostic.
        :param permissions_boundary: Options for applying a permissions boundary to all IAM Roles and Users created within this Stage. Default: - no permissions boundary is applied
        :param stack_name: Name to deploy the stack with. Default: - Derived from construct path.
        :param suppress_template_indentation: Enable this flag to suppress indentation in generated CloudFormation templates. If not specified, the value of the ``@aws-cdk/core:suppressTemplateIndentation`` context key will be used. If that is not specified, then the default value ``false`` will be used. Default: - the value of ``@aws-cdk/core:suppressTemplateIndentation``, or ``false`` if that is not set.
        :param synthesizer: Synthesis method to use while deploying this stack. The Stack Synthesizer controls aspects of synthesis and deployment, like how assets are referenced and what IAM roles to use. For more information, see the README of the main CDK package. If not specified, the ``defaultStackSynthesizer`` from ``App`` will be used. If that is not specified, ``DefaultStackSynthesizer`` is used if ``@aws-cdk/core:newStyleStackSynthesis`` is set to ``true`` or the CDK major version is v2. In CDK v1 ``LegacyStackSynthesizer`` is the default if no other synthesizer is specified. Default: - The synthesizer specified on ``App``, or ``DefaultStackSynthesizer`` otherwise.
        :param tags: Stack tags that will be applied to all the taggable resources and the stack itself. Default: {}
        :param termination_protection: Whether to enable termination protection for this stack. Default: false
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__15a9a33311b5aa41f122528e87925d8662e0815e5f09d7988e374cfdea050a91)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument stage", value=stage, expected_type=type_hints["stage"])
        stack_props = _aws_cdk_ceddda9d.StackProps(
            analytics_reporting=analytics_reporting,
            cross_region_references=cross_region_references,
            description=description,
            env=env,
            permissions_boundary=permissions_boundary,
            stack_name=stack_name,
            suppress_template_indentation=suppress_template_indentation,
            synthesizer=synthesizer,
            tags=tags,
            termination_protection=termination_protection,
        )

        jsii.create(self.__class__, self, [scope, id, stage, stack_props])

    @jsii.member(jsii_name="addDependency")
    def add_dependency(
        self,
        target: _aws_cdk_ceddda9d.Stack,
        reason: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Use ``addDependency`` for dependencies between stacks in an ExpressStage.

        Otherwise, use ``addExpressDependency``
        to construct the Pipeline of stacks between Waves and Stages.

        :param target: -
        :param reason: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bcc587ab6bc13caffa524be9c0320a53ca9f80c4fc7c757ceffb0008ac347573)
            check_type(argname="argument target", value=target, expected_type=type_hints["target"])
            check_type(argname="argument reason", value=reason, expected_type=type_hints["reason"])
        return typing.cast(None, jsii.invoke(self, "addDependency", [target, reason]))

    @jsii.member(jsii_name="addExpressDependency")
    def add_express_dependency(
        self,
        target: "ExpressStack",
        reason: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Only use to create dependencies between Stacks in Waves and Stages for building the Pipeline, where having cyclic dependencies is not possible.

        If the ``addExpressDependency`` is used outside the Pipeline construction,
        it will not be safe. Use ``addDependency`` to create stack dependency within the same Stage.

        :param target: -
        :param reason: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__879d590ae5362b889422ff44e98e8fdc081b30ab75c3f73bb791f1e59cffa2be)
            check_type(argname="argument target", value=target, expected_type=type_hints["target"])
            check_type(argname="argument reason", value=reason, expected_type=type_hints["reason"])
        return typing.cast(None, jsii.invoke(self, "addExpressDependency", [target, reason]))

    @jsii.member(jsii_name="expressDependencies")
    def express_dependencies(self) -> typing.List["ExpressStack"]:
        '''The ExpressStack dependencies of the stack.'''
        return typing.cast(typing.List["ExpressStack"], jsii.invoke(self, "expressDependencies", []))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The stack identifier which is a combination of the wave, stage and stack id.'''
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2a767759dfa5395be6ecc01266961a9c2cc361036411cc35372ee6e11029546c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="stage")
    def stage(self) -> "ExpressStage":
        '''The stage that the stack belongs to.'''
        return typing.cast("ExpressStage", jsii.get(self, "stage"))

    @stage.setter
    def stage(self, value: "ExpressStage") -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2e958c9ef72a2d0c3aaf0f9f1a60e0b6201b1633c81a640e71ca2bbe7f16654f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "stage", value) # pyright: ignore[reportArgumentType]


@jsii.implements(IExpressStage)
class ExpressStage(
    metaclass=jsii.JSIIMeta,
    jsii_type="cdk-express-pipeline.ExpressStage",
):
    '''A CDK Express Pipeline Stage that belongs to an ExpressWave.'''

    def __init__(
        self,
        id: builtins.str,
        wave: "ExpressWave",
        stacks: typing.Optional[typing.Sequence[ExpressStack]] = None,
    ) -> None:
        '''Constructs a new instance of the ExpressStage class.

        :param id: The stage identifier.
        :param wave: The wave that the stage belongs to.
        :param stacks: The ExpressStacks in the stage.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__245ca2826c9b997f2790635ddcfbef04762bc8a2022332e01afc13b949cf70a4)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument wave", value=wave, expected_type=type_hints["wave"])
            check_type(argname="argument stacks", value=stacks, expected_type=type_hints["stacks"])
        jsii.create(self.__class__, self, [id, wave, stacks])

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The stage identifier.'''
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__85b05051a77c643d3ed8a27735fdb1c5115fb33b71da08b5137bf934b65ebe1d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="stacks")
    def stacks(self) -> typing.List[ExpressStack]:
        '''The stacks in the stage.'''
        return typing.cast(typing.List[ExpressStack], jsii.get(self, "stacks"))

    @stacks.setter
    def stacks(self, value: typing.List[ExpressStack]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e05ff1a3d72f333ec26c5d8730168d1024b024fab396ec5decbb16ef55ecdd68)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "stacks", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="wave")
    def wave(self) -> "ExpressWave":
        '''The wave that the stage belongs to.'''
        return typing.cast("ExpressWave", jsii.get(self, "wave"))

    @wave.setter
    def wave(self, value: "ExpressWave") -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7663ce522608a1a19b5783485ae032e41251aa3bcaf50c25d7f5601587b2c86d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wave", value) # pyright: ignore[reportArgumentType]


@jsii.implements(IExpressStageLegacy)
class ExpressStageLegacy(
    metaclass=jsii.JSIIMeta,
    jsii_type="cdk-express-pipeline.ExpressStageLegacy",
):
    '''A stage that holds stacks.'''

    def __init__(
        self,
        id: builtins.str,
        stacks: typing.Optional[typing.Sequence[_aws_cdk_ceddda9d.Stack]] = None,
    ) -> None:
        '''
        :param id: The stage identifier.
        :param stacks: The stacks in the stage.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ef6fafe372848c826b5095466be599af161c0ef85262c4461c5b15946d416d8a)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument stacks", value=stacks, expected_type=type_hints["stacks"])
        jsii.create(self.__class__, self, [id, stacks])

    @jsii.member(jsii_name="addStack")
    def add_stack(self, stack: _aws_cdk_ceddda9d.Stack) -> _aws_cdk_ceddda9d.Stack:
        '''Add a stack to the stage.

        :param stack: The stack to add.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c894af91effb498dcc85f4ce0d7c1ea7cc88b0e9ce46cd0afbe5faba127dcd9a)
            check_type(argname="argument stack", value=stack, expected_type=type_hints["stack"])
        return typing.cast(_aws_cdk_ceddda9d.Stack, jsii.invoke(self, "addStack", [stack]))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The stage identifier.'''
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bf3eb70b31883db55c7481c3af5635274ea0b531152ffc77fbe240d4cf471109)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="stacks")
    def stacks(self) -> typing.List[_aws_cdk_ceddda9d.Stack]:
        '''The stacks in the stage.'''
        return typing.cast(typing.List[_aws_cdk_ceddda9d.Stack], jsii.get(self, "stacks"))

    @stacks.setter
    def stacks(self, value: typing.List[_aws_cdk_ceddda9d.Stack]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4560b751b8175d35b73d56b09336c93f3b65806421e5136ac4b9479b20d4fded)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "stacks", value) # pyright: ignore[reportArgumentType]


@jsii.implements(IExpressWave)
class ExpressWave(
    metaclass=jsii.JSIIMeta,
    jsii_type="cdk-express-pipeline.ExpressWave",
):
    '''A CDK Express Pipeline Wave that contains ExpressStages.'''

    def __init__(
        self,
        id: builtins.str,
        separator: typing.Optional[builtins.str] = None,
        sequential_stages: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Constructs a new instance of the ExpressWave class.

        :param id: The wave identifier.
        :param separator: Separator between the wave, stage and stack ids that are concatenated to form the stack id. Default: '_'.
        :param sequential_stages: If true, the stages in the wave will be executed sequentially. Default: false.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e2d5f3923a6b2ec80e7126dcf3fee4db4c4302e23528b8f1a6b804dbcd52b1bd)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument separator", value=separator, expected_type=type_hints["separator"])
            check_type(argname="argument sequential_stages", value=sequential_stages, expected_type=type_hints["sequential_stages"])
        jsii.create(self.__class__, self, [id, separator, sequential_stages])

    @jsii.member(jsii_name="addStage")
    def add_stage(self, id: builtins.str) -> ExpressStage:
        '''Add an ExpressStage to the wave.

        :param id: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2483221f4b80a77d7fb5425bb01e862bb0faa20975c01571285867e7ebac289a)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        return typing.cast(ExpressStage, jsii.invoke(self, "addStage", [id]))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The wave identifier.'''
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__26db5d9a6d2445284b7c8d5a9e1f799dd10cda56d628bfa4a2a86e736e5b5f5a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="separator")
    def separator(self) -> builtins.str:
        '''Separator between the wave, stage and stack ids that are concatenated to form the final stack id.'''
        return typing.cast(builtins.str, jsii.get(self, "separator"))

    @separator.setter
    def separator(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3d5854ca09bf38f246ea0ad1547c742b4d85ac21de4ecdd25f7fde0b74cee485)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "separator", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="stages")
    def stages(self) -> typing.List[ExpressStage]:
        '''The ExpressStages in the wave.'''
        return typing.cast(typing.List[ExpressStage], jsii.get(self, "stages"))

    @stages.setter
    def stages(self, value: typing.List[ExpressStage]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__397c6edf3478bfddcdbbc65faf7cf101e55552e8c9866bcc82db7287aa7e3727)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "stages", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sequentialStages")
    def sequential_stages(self) -> typing.Optional[builtins.bool]:
        '''If true, the stages in the wave will be executed sequentially.'''
        return typing.cast(typing.Optional[builtins.bool], jsii.get(self, "sequentialStages"))

    @sequential_stages.setter
    def sequential_stages(self, value: typing.Optional[builtins.bool]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__faca2817a2891ad9c62ca6c4294f0d2c4e09a89632dd03f8a2770e04ce81559d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sequentialStages", value) # pyright: ignore[reportArgumentType]


@jsii.implements(IExpressWaveLegacy)
class ExpressWaveLegacy(
    metaclass=jsii.JSIIMeta,
    jsii_type="cdk-express-pipeline.ExpressWaveLegacy",
):
    '''A CDK Express Pipeline Legacy Wave that contains Legacy Stages.'''

    def __init__(
        self,
        id: builtins.str,
        sequential_stages: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Constructs a new instance of the ExpressWaveLegacy class.

        :param id: The wave identifier.
        :param sequential_stages: If true, the stages in the wave will be executed sequentially. Default: false.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c0081ffdae64cce4db9c69087d8b66bb2d1dadbd8afbb7316e0b3bf8c9efbb03)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument sequential_stages", value=sequential_stages, expected_type=type_hints["sequential_stages"])
        jsii.create(self.__class__, self, [id, sequential_stages])

    @jsii.member(jsii_name="addStage")
    def add_stage(self, id: builtins.str) -> ExpressStageLegacy:
        '''Add a stage to the wave.

        :param id: The stage identifier.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2a5c818dec4565e93efada7052a99392254569073240c5aa57b5dd41234ce08a)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        return typing.cast(ExpressStageLegacy, jsii.invoke(self, "addStage", [id]))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The wave identifier.'''
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @id.setter
    def id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__77354438e2a204945817e7e42750078579440a11efd1bc3059037d1a389dbf4b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "id", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="stages")
    def stages(self) -> typing.List[IExpressStageLegacy]:
        '''The ExpressStages in the wave.'''
        return typing.cast(typing.List[IExpressStageLegacy], jsii.get(self, "stages"))

    @stages.setter
    def stages(self, value: typing.List[IExpressStageLegacy]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e46f4bd7d8ca47367b9b065564e04c58819d2f62dc94c8e21d96cab827ad27cc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "stages", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sequentialStages")
    def sequential_stages(self) -> typing.Optional[builtins.bool]:
        '''If true, the stages in the wave will be executed sequentially.'''
        return typing.cast(typing.Optional[builtins.bool], jsii.get(self, "sequentialStages"))

    @sequential_stages.setter
    def sequential_stages(self, value: typing.Optional[builtins.bool]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bfb40afb352b1f780efc7514fb88ca08543b06d925f6ba10e33a7afa07d236db)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sequentialStages", value) # pyright: ignore[reportArgumentType]


__all__ = [
    "CdkExpressPipeline",
    "CdkExpressPipelineLegacy",
    "CdkExpressPipelineProps",
    "ExpressStack",
    "ExpressStage",
    "ExpressStageLegacy",
    "ExpressWave",
    "ExpressWaveLegacy",
    "ExpressWaveProps",
    "IExpressStack",
    "IExpressStage",
    "IExpressStageLegacy",
    "IExpressWave",
    "IExpressWaveLegacy",
]

publication.publish()

def _typecheckingstub__51d5a812c29abca46e9446db3e0acfaedb3fb0f70a5ccbc26b8b26b62c731b30(
    id: builtins.str,
    sequential_stages: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e18d77fb9496cb5fdeabb0fe5a14c3dcd08b7a4747694ac0a799b01dfa105a34(
    waves: typing.Sequence[IExpressWave],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ddf3f54429b9cebdd63080df8e42a8f0bee80ea5889f7848d8110f99befcf433(
    waves: typing.Optional[typing.Sequence[IExpressWave]] = None,
    print: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5e78d8fa8554a29ac59173413b98062741ae83aeb4754f02a80c85c27e16d8ce(
    waves: typing.Optional[typing.Sequence[IExpressWaveLegacy]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__58733341409ff8a6c60fbf06de891a31f81f41cf55e7503aaa0238ee46ff5166(
    id: builtins.str,
    sequential_stages: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6d22fe922729d650ca61abf0f4568bb8cbafe791434481f3e0cce74d098f785e(
    waves: typing.Sequence[IExpressWaveLegacy],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0c7d8bd5a65c1437ed17046edfb50f14e1f2b8f73c9db08927132a10f37d409d(
    waves: typing.Optional[typing.Sequence[IExpressWaveLegacy]] = None,
    print: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__54082bd27a8ceffd74f1b6a0cb05b3bbcf4ffa9ada94c72e52e645687ad4ad5b(
    value: typing.List[IExpressWaveLegacy],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cc99a79d5da23f439f19b4717a315983fa455ec2ae7d0300ac3d7381d5892205(
    *,
    separator: typing.Optional[builtins.str] = None,
    waves: typing.Optional[typing.Sequence[ExpressWave]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d91dc79595e990d6da1a185afde4e65465da1f5dc12abd5220e16803db5481a2(
    *,
    id: builtins.str,
    separator: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__76bd73c874b49b4683b044d917cc6800ed471f2b41d3164b902c206407432cbe(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__61a812768afc62205a9db0f1f9d01095658800d0cc43087913d4c1645cde7bdd(
    value: ExpressStage,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0a14719acbf68f0fd518f950b2dd5d2922f8e4c9c9273c2f85d05589af97f191(
    target: ExpressStack,
    reason: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fbca333d17cf67f3ebc52a25d3e08fdc38766f46ae2bcaeff4c01e2edbbd5dce(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d28e54cfe0e98d05cd17fa7ea13e156a82d091df55640c4094698ec7e78ed884(
    value: typing.List[ExpressStack],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ce620906fddfafba1ff8377098c5f9c35ada5694e2e5c6f9d15368e7d1d4c517(
    value: ExpressWave,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2fdf2493af932e5d33d989d572f161b8c998d0298e6a848f0a7af5edeca7b052(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fffd047542b1ad122d53335fcab6ee350d782b3038d2efbf3f05152a18e8559c(
    value: typing.List[_aws_cdk_ceddda9d.Stack],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8030e0d36f67ca6d88248c3aebc00cb88a9491700acbd6c7d3e4f5f06dcff718(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2deeb751aa022d2277fc1af871b8a9419aaef6e789a22f82063f21230a6d03fa(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c33defa4497d6fd82c65487c1c51107af3c835ae4d7e1216f929dd314edaca26(
    value: typing.List[ExpressStage],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ae1159ae328148533b46258d902359880ce2c3976c0b7e6fc201ec69c017e429(
    value: typing.Optional[builtins.bool],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d0c0680f13cf234d76dc5ad77fd9b99005e303ff37a88d475016ab8e65495bbf(
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ebcd93f3691046bc34c345a2d0c5fd123d149d6852a73f251c4a5caeef0b161a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c8bc3fea3bdc86a865ca6e2fcf12e74fb6190d42fb2b51e85f0be6ed539336b3(
    value: typing.List[IExpressStageLegacy],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__344bf89503483c6b8c5fcb2f9805b54198866f417be91cb3b67b3d568e301831(
    value: typing.Optional[builtins.bool],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__15a9a33311b5aa41f122528e87925d8662e0815e5f09d7988e374cfdea050a91(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    stage: ExpressStage,
    *,
    analytics_reporting: typing.Optional[builtins.bool] = None,
    cross_region_references: typing.Optional[builtins.bool] = None,
    description: typing.Optional[builtins.str] = None,
    env: typing.Optional[typing.Union[_aws_cdk_ceddda9d.Environment, typing.Dict[builtins.str, typing.Any]]] = None,
    permissions_boundary: typing.Optional[_aws_cdk_ceddda9d.PermissionsBoundary] = None,
    stack_name: typing.Optional[builtins.str] = None,
    suppress_template_indentation: typing.Optional[builtins.bool] = None,
    synthesizer: typing.Optional[_aws_cdk_ceddda9d.IStackSynthesizer] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    termination_protection: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bcc587ab6bc13caffa524be9c0320a53ca9f80c4fc7c757ceffb0008ac347573(
    target: _aws_cdk_ceddda9d.Stack,
    reason: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__879d590ae5362b889422ff44e98e8fdc081b30ab75c3f73bb791f1e59cffa2be(
    target: ExpressStack,
    reason: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2a767759dfa5395be6ecc01266961a9c2cc361036411cc35372ee6e11029546c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2e958c9ef72a2d0c3aaf0f9f1a60e0b6201b1633c81a640e71ca2bbe7f16654f(
    value: ExpressStage,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__245ca2826c9b997f2790635ddcfbef04762bc8a2022332e01afc13b949cf70a4(
    id: builtins.str,
    wave: ExpressWave,
    stacks: typing.Optional[typing.Sequence[ExpressStack]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__85b05051a77c643d3ed8a27735fdb1c5115fb33b71da08b5137bf934b65ebe1d(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e05ff1a3d72f333ec26c5d8730168d1024b024fab396ec5decbb16ef55ecdd68(
    value: typing.List[ExpressStack],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7663ce522608a1a19b5783485ae032e41251aa3bcaf50c25d7f5601587b2c86d(
    value: ExpressWave,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ef6fafe372848c826b5095466be599af161c0ef85262c4461c5b15946d416d8a(
    id: builtins.str,
    stacks: typing.Optional[typing.Sequence[_aws_cdk_ceddda9d.Stack]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c894af91effb498dcc85f4ce0d7c1ea7cc88b0e9ce46cd0afbe5faba127dcd9a(
    stack: _aws_cdk_ceddda9d.Stack,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bf3eb70b31883db55c7481c3af5635274ea0b531152ffc77fbe240d4cf471109(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4560b751b8175d35b73d56b09336c93f3b65806421e5136ac4b9479b20d4fded(
    value: typing.List[_aws_cdk_ceddda9d.Stack],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e2d5f3923a6b2ec80e7126dcf3fee4db4c4302e23528b8f1a6b804dbcd52b1bd(
    id: builtins.str,
    separator: typing.Optional[builtins.str] = None,
    sequential_stages: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2483221f4b80a77d7fb5425bb01e862bb0faa20975c01571285867e7ebac289a(
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__26db5d9a6d2445284b7c8d5a9e1f799dd10cda56d628bfa4a2a86e736e5b5f5a(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3d5854ca09bf38f246ea0ad1547c742b4d85ac21de4ecdd25f7fde0b74cee485(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__397c6edf3478bfddcdbbc65faf7cf101e55552e8c9866bcc82db7287aa7e3727(
    value: typing.List[ExpressStage],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__faca2817a2891ad9c62ca6c4294f0d2c4e09a89632dd03f8a2770e04ce81559d(
    value: typing.Optional[builtins.bool],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c0081ffdae64cce4db9c69087d8b66bb2d1dadbd8afbb7316e0b3bf8c9efbb03(
    id: builtins.str,
    sequential_stages: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2a5c818dec4565e93efada7052a99392254569073240c5aa57b5dd41234ce08a(
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__77354438e2a204945817e7e42750078579440a11efd1bc3059037d1a389dbf4b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e46f4bd7d8ca47367b9b065564e04c58819d2f62dc94c8e21d96cab827ad27cc(
    value: typing.List[IExpressStageLegacy],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bfb40afb352b1f780efc7514fb88ca08543b06d925f6ba10e33a7afa07d236db(
    value: typing.Optional[builtins.bool],
) -> None:
    """Type checking stubs"""
    pass

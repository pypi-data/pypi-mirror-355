r'''
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](https://makeapullrequest.com)
[![GitHub](https://img.shields.io/github/license/pepperize/cdk-ssm-parameters-cross-region?style=flat-square)](https://github.com/pepperize/cdk-ssm-parameters-cross-region/blob/main/LICENSE)
[![npm (scoped)](https://img.shields.io/npm/v/@pepperize/cdk-ssm-parameters-cross-region?style=flat-square)](https://www.npmjs.com/package/@pepperize/cdk-ssm-parameters-cross-region)
[![PyPI](https://img.shields.io/pypi/v/pepperize.cdk-ssm-parameters-cross-region?style=flat-square)](https://pypi.org/project/pepperize.cdk-ssm-parameters-cross-region/)
[![Nuget](https://img.shields.io/nuget/v/Pepperize.CDK.SsmParametersCrossRegion?style=flat-square)](https://www.nuget.org/packages/Pepperize.CDK.SsmParametersCrossRegion/)
[![Sonatype Nexus (Releases)](https://img.shields.io/nexus/r/com.pepperize/cdk-ssm-parameters-cross-region?server=https%3A%2F%2Fs01.oss.sonatype.org%2F&style=flat-square)](https://s01.oss.sonatype.org/content/repositories/releases/com/pepperize/cdk-ssm-parameters-cross-region/)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/actions/workflow/status/pepperize/cdk-ssm-parameters-cross-region/release.yml?branch=main&label=release&style=flat-square)](https://github.com/pepperize/cdk-ssm-parameters-cross-region/actions/workflows/release.yml)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/pepperize/cdk-ssm-parameters-cross-region?sort=semver&style=flat-square)](https://github.com/pepperize/cdk-ssm-parameters-cross-region/releases)
[![Gitpod ready-to-code](https://img.shields.io/badge/Gitpod-ready--to--code-blue?logo=gitpod&style=flat-square)](https://gitpod.io/#https://github.com/pepperize/cdk-ssm-parameters-cross-region)

# CDK SSM Parameters cross-region

Store, read and lookup AWS SSM Parameters cross-region

> Currently, only supports StringParameter except simple name. Implements `aws_ssm.IParameter` and can be used as `aws_ssm.StringParameter` replacement.

## Install

### TypeScript

```shell
npm install @pepperize/cdk-ssm-parameters-cross-region
```

or

```shell
yarn add @pepperize/cdk-ssm-parameters-cross-region
```

### Python

```shell
pip install pepperize.cdk-ssm-parameters-cross-region
```

### C# / .Net

```
dotnet add package Pepperize.CDK.SsmParametersCrossRegion
```

### Java

```xml
<dependency>
  <groupId>com.pepperize</groupId>
  <artifactId>cdk-ssm-parameters-cross-region</artifactId>
  <version>${cdkSsmParametersCrossRegion.version}</version>
</dependency>
```

## Usage

### Store AWS SSM Parameter cross-region

```python
new StringParameter(scope, "PutParameter", {
  region: "eu-central-1",
  parameterName: "/path/name/example",
  stringValue: "Say hello from another region",
});
```

See [StringParameter](https://github.com/pepperize/cdk-ssm-parameters-cross-region/blob/main//API.md#stringparameter-)

### Read AWS SSM Parameter cross-region

```python
StringParameter.fromStringParameterName(scope, "GetParameter", "eu-central-1", "/path/name/example");
```

See [StringParameter.fromStringParameterName](https://github.com/pepperize/cdk-ssm-parameters-cross-region/blob/main//API.md#fromstringparametername-)

### Lookup AWS SSM Parameter cross-region

```python
StringParameter.valueFromLookup(scope, "eu-central-1", "/path/name/example");
```

See [StringParameter.valueFromLookup](https://github.com/pepperize/cdk-ssm-parameters-cross-region/blob/main//API.md#valuefromlookup-)
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
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import aws_cdk.aws_ssm as _aws_cdk_aws_ssm_ceddda9d
import constructs as _constructs_77d1e7e8


@jsii.implements(_aws_cdk_aws_ssm_ceddda9d.IStringParameter, _aws_cdk_aws_ssm_ceddda9d.IParameter)
class StringParameter(
    _aws_cdk_ceddda9d.Resource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@pepperize/cdk-ssm-parameters-cross-region.StringParameter",
):
    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        parameter_name: builtins.str,
        region: builtins.str,
        string_value: builtins.str,
        allowed_pattern: typing.Optional[builtins.str] = None,
        data_type: typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterDataType] = None,
        description: typing.Optional[builtins.str] = None,
        removal_policy: typing.Optional[_aws_cdk_ceddda9d.RemovalPolicy] = None,
        tier: typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterTier] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param parameter_name: The name of the parameter. It may not be a Default: - a name will be generated by CloudFormation
        :param region: The region to create the parameter in. See AWS.SSM.region for more information.
        :param string_value: The value of the parameter. It may not reference another parameter and ``{{}}`` cannot be used in the value.
        :param allowed_pattern: A regular expression used to validate the parameter value. Default: - undefined, no validation is performed
        :param data_type: The data type of the parameter, such as ``text`` or ``aws:ec2:image``. Default: - undefined
        :param description: Information about the parameter that you want to add to the system. Default: - undefined
        :param removal_policy: Whether to retain or delete the parameter on CloudFormation delete event. Default: - DESTROY
        :param tier: The tier of the string parameter. Default: - undefined
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a1dbce2fa2ceed9bca867403a768a46c247336ba8136347015d7e640bd2714a7)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = StringParameterProps(
            parameter_name=parameter_name,
            region=region,
            string_value=string_value,
            allowed_pattern=allowed_pattern,
            data_type=data_type,
            description=description,
            removal_policy=removal_policy,
            tier=tier,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="fromStringParameterAttributes")
    @builtins.classmethod
    def from_string_parameter_attributes(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        region: builtins.str,
        type: typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterType] = None,
        version: typing.Optional[jsii.Number] = None,
        parameter_name: builtins.str,
        simple_name: typing.Optional[builtins.bool] = None,
    ) -> _aws_cdk_aws_ssm_ceddda9d.IStringParameter:
        '''Imports an external string parameter with name and optional version.

        :param scope: -
        :param id: -
        :param region: The region to retrieve the parameter from. See AWS.SSM.region for more information.
        :param type: The type of the string parameter. Default: ParameterType.STRING
        :param version: The version number of the value you wish to retrieve. Default: The latest version will be retrieved.
        :param parameter_name: The name of the parameter store value. This value can be a token or a concrete string. If it is a concrete string and includes "/" it must also be prefixed with a "/" (fully-qualified).
        :param simple_name: Indicates of the parameter name is a simple name (i.e. does not include "/" separators). This is only required only if ``parameterName`` is a token, which means we are unable to detect if the name is simple or "path-like" for the purpose of rendering SSM parameter ARNs. If ``parameterName`` is not specified, ``simpleName`` must be ``true`` (or undefined) since the name generated by AWS CloudFormation is always a simple name. Default: - auto-detect based on ``parameterName``
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__01e536e68070f5950f8d602ebb785fe1287210e51a21ecd0d04e72f10c57e066)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        attrs = StringParameterAttributes(
            region=region,
            type=type,
            version=version,
            parameter_name=parameter_name,
            simple_name=simple_name,
        )

        return typing.cast(_aws_cdk_aws_ssm_ceddda9d.IStringParameter, jsii.sinvoke(cls, "fromStringParameterAttributes", [scope, id, attrs]))

    @jsii.member(jsii_name="fromStringParameterName")
    @builtins.classmethod
    def from_string_parameter_name(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        region: builtins.str,
        parameter_name: builtins.str,
    ) -> _aws_cdk_aws_ssm_ceddda9d.IStringParameter:
        '''Imports an external string parameter by name and region.

        :param scope: -
        :param id: -
        :param region: -
        :param parameter_name: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d442daa1706014f1b04f6498688c3408c9e86923fb2fcfa175a8170f5a5fba63)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument region", value=region, expected_type=type_hints["region"])
            check_type(argname="argument parameter_name", value=parameter_name, expected_type=type_hints["parameter_name"])
        return typing.cast(_aws_cdk_aws_ssm_ceddda9d.IStringParameter, jsii.sinvoke(cls, "fromStringParameterName", [scope, id, region, parameter_name]))

    @jsii.member(jsii_name="valueFromLookup")
    @builtins.classmethod
    def value_from_lookup(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        region: builtins.str,
        parameter_name: builtins.str,
    ) -> builtins.str:
        '''Reads the value of an SSM parameter during synthesis through an environmental context provider.

        Requires that the stack this scope is defined in will have explicit
        account information. Otherwise, it will fail during synthesis.

        :param scope: -
        :param region: -
        :param parameter_name: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__10597bc8a55d8c6578585c999111a0c480e02daa0cf199fb03676b34601b3bbb)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument region", value=region, expected_type=type_hints["region"])
            check_type(argname="argument parameter_name", value=parameter_name, expected_type=type_hints["parameter_name"])
        return typing.cast(builtins.str, jsii.sinvoke(cls, "valueFromLookup", [scope, region, parameter_name]))

    @jsii.member(jsii_name="grantRead")
    def grant_read(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''Grants read (DescribeParameter, GetParameter, GetParameterHistory) permissions on the SSM Parameter.

        :param grantee: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2f1ca986f4d1b557fd527669e0a952b36b02c5775a61aafb72c33a348b2a8230)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantRead", [grantee]))

    @jsii.member(jsii_name="grantWrite")
    def grant_write(
        self,
        grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
    ) -> _aws_cdk_aws_iam_ceddda9d.Grant:
        '''Grants write (PutParameter) permissions on the SSM Parameter.

        :param grantee: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4cdbc0640aadf0680ae287ae5c113c1f62ec38dc84c782b6d64848f8e10c6bbf)
            check_type(argname="argument grantee", value=grantee, expected_type=type_hints["grantee"])
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Grant, jsii.invoke(self, "grantWrite", [grantee]))

    @builtins.property
    @jsii.member(jsii_name="parameterArn")
    def parameter_arn(self) -> builtins.str:
        '''The ARN of the SSM Parameter resource.'''
        return typing.cast(builtins.str, jsii.get(self, "parameterArn"))

    @builtins.property
    @jsii.member(jsii_name="parameterName")
    def parameter_name(self) -> builtins.str:
        '''The name of the SSM Parameter resource.'''
        return typing.cast(builtins.str, jsii.get(self, "parameterName"))

    @builtins.property
    @jsii.member(jsii_name="parameterType")
    def parameter_type(self) -> builtins.str:
        '''The type of the SSM Parameter resource.'''
        return typing.cast(builtins.str, jsii.get(self, "parameterType"))

    @builtins.property
    @jsii.member(jsii_name="stringValue")
    def string_value(self) -> builtins.str:
        '''The parameter value.

        Value must not nest another parameter. Do not use {{}} in the value.
        '''
        return typing.cast(builtins.str, jsii.get(self, "stringValue"))

    @builtins.property
    @jsii.member(jsii_name="tags")
    def tags(self) -> _aws_cdk_ceddda9d.TagManager:
        return typing.cast(_aws_cdk_ceddda9d.TagManager, jsii.get(self, "tags"))


@jsii.data_type(
    jsii_type="@pepperize/cdk-ssm-parameters-cross-region.StringParameterAttributes",
    jsii_struct_bases=[_aws_cdk_aws_ssm_ceddda9d.StringParameterAttributes],
    name_mapping={
        "parameter_name": "parameterName",
        "simple_name": "simpleName",
        "type": "type",
        "version": "version",
        "region": "region",
    },
)
class StringParameterAttributes(_aws_cdk_aws_ssm_ceddda9d.StringParameterAttributes):
    def __init__(
        self,
        *,
        parameter_name: builtins.str,
        simple_name: typing.Optional[builtins.bool] = None,
        type: typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterType] = None,
        version: typing.Optional[jsii.Number] = None,
        region: builtins.str,
    ) -> None:
        '''
        :param parameter_name: The name of the parameter store value. This value can be a token or a concrete string. If it is a concrete string and includes "/" it must also be prefixed with a "/" (fully-qualified).
        :param simple_name: Indicates of the parameter name is a simple name (i.e. does not include "/" separators). This is only required only if ``parameterName`` is a token, which means we are unable to detect if the name is simple or "path-like" for the purpose of rendering SSM parameter ARNs. If ``parameterName`` is not specified, ``simpleName`` must be ``true`` (or undefined) since the name generated by AWS CloudFormation is always a simple name. Default: - auto-detect based on ``parameterName``
        :param type: The type of the string parameter. Default: ParameterType.STRING
        :param version: The version number of the value you wish to retrieve. Default: The latest version will be retrieved.
        :param region: The region to retrieve the parameter from. See AWS.SSM.region for more information.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3579c46e8be7aaa49bdc9227a9b4b7d96dd8e48c5e2503fc99ff127bd9017282)
            check_type(argname="argument parameter_name", value=parameter_name, expected_type=type_hints["parameter_name"])
            check_type(argname="argument simple_name", value=simple_name, expected_type=type_hints["simple_name"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
            check_type(argname="argument region", value=region, expected_type=type_hints["region"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "parameter_name": parameter_name,
            "region": region,
        }
        if simple_name is not None:
            self._values["simple_name"] = simple_name
        if type is not None:
            self._values["type"] = type
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def parameter_name(self) -> builtins.str:
        '''The name of the parameter store value.

        This value can be a token or a concrete string. If it is a concrete string
        and includes "/" it must also be prefixed with a "/" (fully-qualified).
        '''
        result = self._values.get("parameter_name")
        assert result is not None, "Required property 'parameter_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def simple_name(self) -> typing.Optional[builtins.bool]:
        '''Indicates of the parameter name is a simple name (i.e. does not include "/" separators).

        This is only required only if ``parameterName`` is a token, which means we
        are unable to detect if the name is simple or "path-like" for the purpose
        of rendering SSM parameter ARNs.

        If ``parameterName`` is not specified, ``simpleName`` must be ``true`` (or
        undefined) since the name generated by AWS CloudFormation is always a
        simple name.

        :default: - auto-detect based on ``parameterName``
        '''
        result = self._values.get("simple_name")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def type(self) -> typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterType]:
        '''The type of the string parameter.

        :default: ParameterType.STRING
        '''
        result = self._values.get("type")
        return typing.cast(typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterType], result)

    @builtins.property
    def version(self) -> typing.Optional[jsii.Number]:
        '''The version number of the value you wish to retrieve.

        :default: The latest version will be retrieved.
        '''
        result = self._values.get("version")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def region(self) -> builtins.str:
        '''The region to retrieve the parameter from.

        See AWS.SSM.region for more information.
        '''
        result = self._values.get("region")
        assert result is not None, "Required property 'region' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StringParameterAttributes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@pepperize/cdk-ssm-parameters-cross-region.StringParameterProps",
    jsii_struct_bases=[],
    name_mapping={
        "parameter_name": "parameterName",
        "region": "region",
        "string_value": "stringValue",
        "allowed_pattern": "allowedPattern",
        "data_type": "dataType",
        "description": "description",
        "removal_policy": "removalPolicy",
        "tier": "tier",
    },
)
class StringParameterProps:
    def __init__(
        self,
        *,
        parameter_name: builtins.str,
        region: builtins.str,
        string_value: builtins.str,
        allowed_pattern: typing.Optional[builtins.str] = None,
        data_type: typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterDataType] = None,
        description: typing.Optional[builtins.str] = None,
        removal_policy: typing.Optional[_aws_cdk_ceddda9d.RemovalPolicy] = None,
        tier: typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterTier] = None,
    ) -> None:
        '''Properties needed to create a String SSM parameter.

        :param parameter_name: The name of the parameter. It may not be a Default: - a name will be generated by CloudFormation
        :param region: The region to create the parameter in. See AWS.SSM.region for more information.
        :param string_value: The value of the parameter. It may not reference another parameter and ``{{}}`` cannot be used in the value.
        :param allowed_pattern: A regular expression used to validate the parameter value. Default: - undefined, no validation is performed
        :param data_type: The data type of the parameter, such as ``text`` or ``aws:ec2:image``. Default: - undefined
        :param description: Information about the parameter that you want to add to the system. Default: - undefined
        :param removal_policy: Whether to retain or delete the parameter on CloudFormation delete event. Default: - DESTROY
        :param tier: The tier of the string parameter. Default: - undefined
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__45f8a685875be7172ad63f8dded88f74a9b92986fb8728ed45b207d027f47aa8)
            check_type(argname="argument parameter_name", value=parameter_name, expected_type=type_hints["parameter_name"])
            check_type(argname="argument region", value=region, expected_type=type_hints["region"])
            check_type(argname="argument string_value", value=string_value, expected_type=type_hints["string_value"])
            check_type(argname="argument allowed_pattern", value=allowed_pattern, expected_type=type_hints["allowed_pattern"])
            check_type(argname="argument data_type", value=data_type, expected_type=type_hints["data_type"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument removal_policy", value=removal_policy, expected_type=type_hints["removal_policy"])
            check_type(argname="argument tier", value=tier, expected_type=type_hints["tier"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "parameter_name": parameter_name,
            "region": region,
            "string_value": string_value,
        }
        if allowed_pattern is not None:
            self._values["allowed_pattern"] = allowed_pattern
        if data_type is not None:
            self._values["data_type"] = data_type
        if description is not None:
            self._values["description"] = description
        if removal_policy is not None:
            self._values["removal_policy"] = removal_policy
        if tier is not None:
            self._values["tier"] = tier

    @builtins.property
    def parameter_name(self) -> builtins.str:
        '''The name of the parameter.

        It may not be a

        :default: - a name will be generated by CloudFormation
        '''
        result = self._values.get("parameter_name")
        assert result is not None, "Required property 'parameter_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def region(self) -> builtins.str:
        '''The region to create the parameter in.

        See AWS.SSM.region for more information.
        '''
        result = self._values.get("region")
        assert result is not None, "Required property 'region' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def string_value(self) -> builtins.str:
        '''The value of the parameter.

        It may not reference another parameter and ``{{}}`` cannot be used in the value.
        '''
        result = self._values.get("string_value")
        assert result is not None, "Required property 'string_value' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def allowed_pattern(self) -> typing.Optional[builtins.str]:
        '''A regular expression used to validate the parameter value.

        :default: - undefined, no validation is performed
        '''
        result = self._values.get("allowed_pattern")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def data_type(self) -> typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterDataType]:
        '''The data type of the parameter, such as ``text`` or ``aws:ec2:image``.

        :default: - undefined
        '''
        result = self._values.get("data_type")
        return typing.cast(typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterDataType], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Information about the parameter that you want to add to the system.

        :default: - undefined
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def removal_policy(self) -> typing.Optional[_aws_cdk_ceddda9d.RemovalPolicy]:
        '''Whether to retain or delete the parameter on CloudFormation delete event.

        :default: - DESTROY
        '''
        result = self._values.get("removal_policy")
        return typing.cast(typing.Optional[_aws_cdk_ceddda9d.RemovalPolicy], result)

    @builtins.property
    def tier(self) -> typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterTier]:
        '''The tier of the string parameter.

        :default: - undefined
        '''
        result = self._values.get("tier")
        return typing.cast(typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterTier], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StringParameterProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "StringParameter",
    "StringParameterAttributes",
    "StringParameterProps",
]

publication.publish()

def _typecheckingstub__a1dbce2fa2ceed9bca867403a768a46c247336ba8136347015d7e640bd2714a7(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    parameter_name: builtins.str,
    region: builtins.str,
    string_value: builtins.str,
    allowed_pattern: typing.Optional[builtins.str] = None,
    data_type: typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterDataType] = None,
    description: typing.Optional[builtins.str] = None,
    removal_policy: typing.Optional[_aws_cdk_ceddda9d.RemovalPolicy] = None,
    tier: typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterTier] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__01e536e68070f5950f8d602ebb785fe1287210e51a21ecd0d04e72f10c57e066(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    region: builtins.str,
    type: typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterType] = None,
    version: typing.Optional[jsii.Number] = None,
    parameter_name: builtins.str,
    simple_name: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d442daa1706014f1b04f6498688c3408c9e86923fb2fcfa175a8170f5a5fba63(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    region: builtins.str,
    parameter_name: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__10597bc8a55d8c6578585c999111a0c480e02daa0cf199fb03676b34601b3bbb(
    scope: _constructs_77d1e7e8.Construct,
    region: builtins.str,
    parameter_name: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2f1ca986f4d1b557fd527669e0a952b36b02c5775a61aafb72c33a348b2a8230(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4cdbc0640aadf0680ae287ae5c113c1f62ec38dc84c782b6d64848f8e10c6bbf(
    grantee: _aws_cdk_aws_iam_ceddda9d.IGrantable,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3579c46e8be7aaa49bdc9227a9b4b7d96dd8e48c5e2503fc99ff127bd9017282(
    *,
    parameter_name: builtins.str,
    simple_name: typing.Optional[builtins.bool] = None,
    type: typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterType] = None,
    version: typing.Optional[jsii.Number] = None,
    region: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__45f8a685875be7172ad63f8dded88f74a9b92986fb8728ed45b207d027f47aa8(
    *,
    parameter_name: builtins.str,
    region: builtins.str,
    string_value: builtins.str,
    allowed_pattern: typing.Optional[builtins.str] = None,
    data_type: typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterDataType] = None,
    description: typing.Optional[builtins.str] = None,
    removal_policy: typing.Optional[_aws_cdk_ceddda9d.RemovalPolicy] = None,
    tier: typing.Optional[_aws_cdk_aws_ssm_ceddda9d.ParameterTier] = None,
) -> None:
    """Type checking stubs"""
    pass

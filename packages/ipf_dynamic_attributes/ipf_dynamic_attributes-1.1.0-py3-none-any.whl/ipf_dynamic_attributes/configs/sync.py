from functools import cached_property
from typing import Optional, Literal, Any, Union, Callable, ForwardRef

from httpx import Timeout
from pydantic import BaseModel, Field, model_validator, RootModel, ConfigDict

from ipf_dynamic_attributes.configs.rules import InventoryRule, DefaultRule, ConfigRule, TableRule, DefaultConfigRule

Config = ForwardRef("Config")


class IPFabric(BaseModel):
    base_url: Optional[str] = Field(
        None,
        description="The IP Fabric Base URL to fetch data from (env: 'IPF_URL').",
        title="IP Fabric URL",
        examples=["https://demo.ipfabric.com"],
    )
    auth: Optional[str] = Field(
        None,
        description="The IP Fabric API token to use for authentication (env: 'IPF_TOKEN'). "
        "Username and password can be used by setting Environment Variables (IPF_USERNAME, IPF_PASSWORD).",
        title="IP Fabric API Token",
    )
    timeout: Optional[Union[int, tuple, float, None]] = Field(
        5,
        description="The timeout for the API requests; default 5 seconds (env: 'IPF_TIMEOUT').",
        title="IP Fabric Timeout",
    )
    verify: Union[bool, str] = Field(
        True, description="Verify SSL Certificates; default True (env: 'IPF_VERIFY').", title="SSL Verification"
    )
    snapshot_id: str = Field(
        "$last",
        description="The snapshot ID to use for the API endpoint; defaults to '$last'.",
        title="Snapshot ID",
        examples=["$last", "$prev", "$lastLocked", "d03a89d3-911b-4e2d-868b-8b8103771801"],
    )


class Config(BaseModel):
    model_config = ConfigDict(extra="allow")

    ipfabric: Optional[IPFabric] = Field(
        default_factory=IPFabric, description="IP Fabric connection configuration.", title="IP Fabric Connection"
    )
    dry_run: bool = Field(
        True, description="Defaults to run in dry-run mode and not apply any updates.", title="Dry Run"
    )
    update_snapshot: bool = Field(
        True,
        description="Update Local Attributes on the selected snapshot; default True.",
        title="Update Snapshot Attributes",
    )
    inventory: InventoryRule = Field(
        default_factory=InventoryRule,
        description="Optional: Filters to limit the inventory of devices based on Inventory > Devices table.",
        title="Inventory Filters",
    )
    default: Optional[DefaultRule] = Field(
        None,
        description="Optional: Default configuration to merge into all other Table Rules.",
        title="Default Table TableRule",
    )
    default_config: Optional[DefaultConfigRule] = Field(
        None,
        description="Optional: Default configuration to merge into all other Configuration Rules.",
        title="Default Configuration TableRule",
    )
    rules: list[Union[ConfigRule, TableRule]] = Field(
        description="List of Table or Configuration Rules which are processed in order; at least 1 rule is required.",
        title="Dynamic Attribute Rules",
    )

    @model_validator(mode="after")
    def _validate(self):
        if not self.rules:
            raise ValueError("At least one rule must be provided.")
        if len({_.name for _ in self.rules}) != len(self.rules):
            raise ValueError("Duplicate TableRule Names found.")
        if False in {bool(_.value) for _ in self.rules} and not self.default.value:
            raise ValueError("All Rules must have a value set or 'default[value]' can be used for Table Rules.")
        if False in {bool(_.attribute) for _ in self.rules if isinstance(_, TableRule)} and not self.default.attribute:
            raise ValueError(
                "An Attribute Name must be set in 'default[attribute]' or all Table rules must have it defined."
            )
        if (
            False in {bool(_.attribute) for _ in self.rules if isinstance(_, ConfigRule)}
            and not self.default_config.attribute
        ):
            raise ValueError(
                "An Attribute Name must be set in 'default_config[attribute]' "
                "or all Configuration Rules must have it defined."
            )
        return self

    @cached_property
    def merged_rules(self) -> list[Union[ConfigRule, TableRule]]:
        """Copy Defaults to rules"""
        return [
            rule.merge_default(self.default if isinstance(rule, TableRule) else self.default_config)
            for rule in self.rules
        ]

    def model_dump_merged(
        self,
        *,
        mode: Literal["json", "python"] = "python",
        context: Optional[Any] = None,
        by_alias: Optional[bool] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: Union[bool, Literal["none", "warn", "error"]] = True,
        fallback: Optional[Callable[[Any], Any]] = None,
        serialize_as_any: bool = False,
    ) -> dict[str, Any]:
        """Dump the full config with all default rules merged."""
        config = self.model_copy(deep=True)
        config.rules = self.merged_rules
        return config.model_dump(
            mode=mode,
            exclude={"default", "default_config"},
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
            fallback=fallback,
            serialize_as_any=serialize_as_any,
        )

    def model_merged(self) -> Config:
        """Return a copy of the merged config with all default rules merged."""
        config = self.model_copy(deep=True)
        config.rules = self.merged_rules
        config.default, config.default_config = None, None
        return config


Config.model_rebuild()


class MultiConfig(RootModel):
    """Root model to handle multiple configurations."""

    root: list[Config] = Field(
        title="IP Fabric Dynamic Attribute Configurations",
        description="Ordered list of Configurations to process; at least one configuration is required. "
        "IPFabric ['base_url', 'auth', 'verify', 'snapshot_id'] values must be the same in all config files; "
        "recommended to leave empty and use environment variables.",
    )

    def _get_ipfabric_config(self, attr: str) -> list[Any]:
        """Get a unique attribute from all configurations."""
        return list(
            {getattr(_.ipfabric, attr) for _ in self.root if _.ipfabric and getattr(_.ipfabric, attr) is not None}
        )

    @model_validator(mode="after")
    def _validate(self):
        if not self.root:
            raise ValueError("At least one configuration must be provided.")
        for attr in ["base_url", "auth", "verify", "snapshot_id"]:
            if len(self._get_ipfabric_config(attr)) > 1:
                raise ValueError(
                    "All IPFabric settings must have the same ['base_url', 'auth', 'verify', 'snapshot_id'] values."
                )
        if len({_.dry_run for _ in self.root}) > 1:
            raise ValueError("All configurations must have the same 'dry_run' value.")
        if len({_.update_snapshot for _ in self.root}) > 1:
            raise ValueError("All configurations must have the same 'update_snapshot' value.")
        return self

    @staticmethod
    def _merge_timeout(timeouts: set) -> Union[int, tuple, float, None]:
        """Merge timeouts from a set of timeouts using the largest value or None."""
        if None in timeouts:
            return None
        i_timeout = sorted({_ for _ in timeouts if not isinstance(_, tuple)}, reverse=True)
        _ = {i_timeout[0]} if i_timeout else set()

        con, read, write, pool = _.copy(), _.copy(), _.copy(), _.copy()
        for t in [Timeout(timeout=_) for _ in timeouts if isinstance(_, tuple)]:
            con.add(t.connect)
            read.add(t.read)
            write.add(t.write)
            pool.add(t.pool)
        return (
            None if None in con else sorted(con, reverse=True)[0],
            None if None in read else sorted(read, reverse=True)[0],
            None if None in write else sorted(write, reverse=True)[0],
            None if None in pool else sorted(pool, reverse=True)[0],
        )

    def _merge_ipf_settings(self) -> IPFabric:
        """Merge IPFabric settings."""
        base_url = self._get_ipfabric_config("base_url")
        auth = self._get_ipfabric_config("auth")
        verify = self._get_ipfabric_config("verify")
        snapshot_id = self._get_ipfabric_config("snapshot_id")
        return IPFabric(
            base_url=base_url[0] if base_url else None,
            auth=auth[0] if auth else None,
            verify=verify[0] if verify else None,
            timeout=self._merge_timeout(set(self._get_ipfabric_config("timeout"))),
            snapshot_id=snapshot_id[0] if snapshot_id else None,
        )

    def merge_configs(self) -> Config:
        """Merge all configurations into a single config file."""
        rules = []
        reports = set()
        for idx, config in enumerate(self.root):
            prefix = config.model_extra.get("filename", f"config_{idx}")
            merged = config.model_merged()
            reports.update(set(merged.inventory.report_columns))
            for rule in merged.rules:
                rule.name = f"{prefix}: {rule.name}"
                rule.inventory = merged.inventory
            rules.extend(merged.rules)

        return Config(
            ipfabric=self._merge_ipf_settings(),
            dry_run=self.root[0].dry_run,
            update_snapshot=self.root[0].update_snapshot,
            inventory=InventoryRule(report_columns=list(reports)),
            rules=rules,
        )

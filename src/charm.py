#!/usr/bin/env python3
# Copyright 2021 Ubuntu
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import logging
import kubernetes

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus

from charms.nginx_ingress_integrator.v0.ingress import IngressRequires

logger = logging.getLogger(__name__)


class RancherCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.rancher_pebble_ready, self._on_rancher_pebble_ready)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.fortune_action, self._on_fortune_action)
        self.framework.observe(self.on.cluster_control_relation_changed, self._on_cluster_control_relation_changed)
        self._stored.set_default(https_listen_port=self.config["https-listen-port"], add_local=self.config["add-local"])

        self.ingress = IngressRequires(self, {"service-hostname": self.config["external_hostname"],
                                      "service-name": self.app.name,
                                      "service-port": 80})

    def _on_rancher_pebble_ready(self, event):
        """Define and start a workload using the Pebble API.

        TEMPLATE-TODO: change this example to suit your needs.
        You'll need to specify the right entrypoint and environment
        configuration for your specific workload. Tip: you can see the
        standard entrypoint of an existing container using docker inspect

        Learn more about Pebble layers at https://github.com/canonical/pebble
        """

        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Define an initial Pebble layer configuration
        pebble_layer = {
            "summary": "rancher layer",
            "description": "pebble config layer for rancher",
            "services": {
                "rancher": {
                    "override": "replace",
                    "summary": "rancher",
                    "command": "entrypoint.sh --https-listen-port=" + str(self.config["https-listen-port"]) + " --add-local=" + str(self.config["add-local"]).lower(),
                    "startup": "enabled",
                    "environment": {
                        "CATTLE_NAMESPACE": self.model.name,
                        "CATTLE_PEER_SERVICE": "rancher",
                        "TINI_SUBREAPER": "true",
                    },
                }
            },
        }
        # Add intial Pebble config layer using the Pebble API
        container.add_layer("rancher", pebble_layer, combine=True)
        # Autostart any services that were defined with startup: enabled
        container.autostart()
        # Learn more about statuses in the SDK docs:
        # https://juju.is/docs/sdk/constructs#heading--statuses
        self.unit.status = ActiveStatus()

    def _on_config_changed(self, _):
        """Just an example to show how to deal with changed configuration.

        TEMPLATE-TODO: change this example to suit your needs.
        If you don't need to handle config, you can remove this method,
        the hook created in __init__.py for it, the corresponding test,
        and the config.py file.

        Learn more about config at https://juju.is/docs/sdk/config
        """
        # current = self.config["thing"]
        # if current not in self._stored.things:
        #     logger.debug("found a new thing: %r", current)
        #     self._stored.things.append(current)

        self.ingress.update_config({"service-hostname": self.config["external_hostname"]})
        s = 5


    def _on_cluster_control_relation_changed(self, event):
        """Just an example to show how to receive actions.

        TEMPLATE-TODO: change this example to suit your needs.
        If you don't need to handle actions, you can remove this method,
        the hook created in __init__.py for it, the corresponding test,
        and the actions.py file.

        Learn more about actions at https://juju.is/docs/sdk/actions
        """
        pass

    def _on_fortune_action(self, event):
        """Just an example to show how to receive actions.

        TEMPLATE-TODO: change this example to suit your needs.
        If you don't need to handle actions, you can remove this method,
        the hook created in __init__.py for it, the corresponding test,
        and the actions.py file.

        Learn more about actions at https://juju.is/docs/sdk/actions
        """
        fail = event.params["fail"]
        if fail:
            event.fail(fail)
        else:
            event.set_results({"fortune": "A bug in the code is worth two in the documentation."})


if __name__ == "__main__":
    main(RancherCharm)
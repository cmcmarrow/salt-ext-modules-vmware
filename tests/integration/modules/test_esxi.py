# Copyright 2021 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
import os
from unittest.mock import MagicMock

import pytest
import salt.exceptions
import saltext.vmware.modules.esxi as esxi
import saltext.vmware.utils.common as utils_common
import saltext.vmware.utils.esxi


def test_esxi_get_lun_ids_should_return_lun_NAA_ids(service_instance, integration_test_config):
    expected_lun_ids = integration_test_config["esxi_datastore_disk_names"]
    actual_ids = esxi.get_lun_ids(service_instance=service_instance)
    assert actual_ids == expected_lun_ids


HOST_CAPABILITIES = [
    "accel3dSupported",
    "backgroundSnapshotsSupported",
    "cloneFromSnapshotSupported",
    "cpuHwMmuSupported",
    "cpuMemoryResourceConfigurationSupported",
    "cryptoSupported",
    "datastorePrincipalSupported",
    "deltaDiskBackingsSupported",
    "eightPlusHostVmfsSharedAccessSupported",
    "encryptedVMotionSupported",
    "encryptionCBRCSupported",
    "encryptionChangeOnAddRemoveSupported",
    "encryptionFaultToleranceSupported",
    "encryptionHBRSupported",
    "encryptionHotOperationSupported",
    "encryptionMemorySaveSupported",
    "encryptionRDMSupported",
    "encryptionVFlashSupported",
    "encryptionWithSnapshotsSupported",
    "featureCapabilitiesSupported",
    "firewallIpRulesSupported",
    "ftCompatibilityIssues",
    "ftSupported",
    "gatewayOnNicSupported",
    "hbrNicSelectionSupported",
    "highGuestMemSupported",
    "hostAccessManagerSupported",
    "interVMCommunicationThroughVMCISupported",
    "ipmiSupported",
    "iscsiSupported",
    "latencySensitivitySupported",
    "localSwapDatastoreSupported",
    "loginBySSLThumbprintSupported",
    "maintenanceModeSupported",
    "markAsLocalSupported",
    "markAsSsdSupported",
    "maxHostRunningVms",
    "maxHostSupportedVcpus",
    "maxNumDisksSVMotion",
    "maxRegisteredVMs",
    "maxRunningVMs",
    "maxSupportedVMs",
    "maxSupportedVcpus",
    "maxVcpusPerFtVm",
    "messageBusProxySupported",
    "multipleNetworkStackInstanceSupported",
    "nestedHVSupported",
    "nfs41Krb5iSupported",
    "nfs41Supported",
    "nfsSupported",
    "nicTeamingSupported",
    "oneKVolumeAPIsSupported",
    "perVMNetworkTrafficShapingSupported",
    "perVmSwapFiles",
    "preAssignedPCIUnitNumbersSupported",
    "provisioningNicSelectionSupported",
    "rebootSupported",
    "recordReplaySupported",
    "recursiveResourcePoolsSupported",
    "reliableMemoryAware",
    "replayCompatibilityIssues",
    "replayUnsupportedReason",
    "restrictedSnapshotRelocateSupported",
    "sanSupported",
    "scaledScreenshotSupported",
    "scheduledHardwareUpgradeSupported",
    "screenshotSupported",
    "servicePackageInfoSupported",
    "shutdownSupported",
    "smartCardAuthenticationSupported",
    "smpFtCompatibilityIssues",
    "smpFtSupported",
    "snapshotRelayoutSupported",
    "standbySupported",
    "storageIORMSupported",
    "storagePolicySupported",
    "storageVMotionSupported",
    "supportedVmfsMajorVersion",
    "suspendedRelocateSupported",
    "tpmSupported",
    "turnDiskLocatorLedSupported",
    "unsharedSwapVMotionSupported",
    "upitSupported",
    "vFlashSupported",
    "vPMCSupported",
    "vStorageCapable",
    "virtualExecUsageSupported",
    "virtualVolumeDatastoreSupported",
    "vlanTaggingSupported",
    "vmDirectPathGen2Supported",
    "vmDirectPathGen2UnsupportedReason",
    "vmDirectPathGen2UnsupportedReasonExtended",
    "vmfsDatastoreMountCapable",
    "vmotionAcrossNetworkSupported",
    "vmotionSupported",
    "vmotionWithStorageVMotionSupported",
    "vrNfcNicSelectionSupported",
    "vsanSupported",
]


def test_esxi_host_capability_params(service_instance, integration_test_config):
    """
    Test we are returning the same values from get_capabilities
    as our connected vcenter instance.
    """
    capabilities = esxi.get_capabilities(service_instance=service_instance)
    for host_id in capabilities:
        for arg_name in HOST_CAPABILITIES:
            assert (
                capabilities[host_id][utils_common.camel_to_snake_case(arg_name)]
                == integration_test_config["esxi_capabilities"][host_id][arg_name]
            )


def test_list_pkgs(service_instance):
    """
    Test list packages on ESXi host
    """
    ret = esxi.list_pkgs(
        service_instance=service_instance,
        datacenter_name="Datacenter",
        cluster_name="Cluster",
    )
    assert ret
    for host in ret:
        assert ret[host]
        for pkg in ret[host]:
            assert sorted(list(ret[host][pkg])) == sorted(
                [
                    "version",
                    "vendor",
                    "summary",
                    "description",
                    "acceptance_level",
                    "maintenance_mode_required",
                    "creation_date",
                ]
            )

    host = MagicMock()
    host.configManager.imageConfigManager.FetchSoftwarePackages.side_effect = (
        salt.exceptions.VMwareApiError
    )
    setattr(saltext.vmware.utils.esxi, "get_hosts", MagicMock(return_value=[host]))
    with pytest.raises(salt.exceptions.SaltException) as exc:
        ret = esxi.list_pkgs(
            service_instance=service_instance,
            datacenter_name="Datacenter",
            cluster_name="Cluster",
        )


def test_manage_service(service_instance):
    """
    Test manage services on esxi host
    """
    SSH_SERVICE = "TSM-SSH"
    ret = esxi.manage_service(
        service_name=SSH_SERVICE,
        service_instance=service_instance,
        state="start",
        datacenter_name="Datacenter",
        cluster_name="Cluster",
    )
    assert ret

    ret = esxi.list_services(
        service_name=SSH_SERVICE,
        service_instance=service_instance,
        datacenter_name="Datacenter",
        cluster_name="Cluster",
    )
    for host in ret:
        assert ret[host][SSH_SERVICE]["state"] == "running"

    ret = esxi.manage_service(
        service_name=SSH_SERVICE,
        service_instance=service_instance,
        state="stop",
        datacenter_name="Datacenter",
        cluster_name="Cluster",
    )
    assert ret

    ret = esxi.list_services(
        service_name=SSH_SERVICE,
        service_instance=service_instance,
        datacenter_name="Datacenter",
        cluster_name="Cluster",
    )
    for host in ret:
        assert ret[host][SSH_SERVICE]["state"] == "stopped"

    ret = esxi.manage_service(
        service_name=SSH_SERVICE,
        service_instance=service_instance,
        state="restart",
        datacenter_name="Datacenter",
        cluster_name="Cluster",
    )
    assert ret
    ret = esxi.list_services(
        service_name=SSH_SERVICE,
        service_instance=service_instance,
        datacenter_name="Datacenter",
        cluster_name="Cluster",
    )
    for host in ret:
        assert ret[host][SSH_SERVICE]["state"] == "running"

    for policy in ["on", "off", "automatic"]:
        ret = esxi.manage_service(
            service_name=SSH_SERVICE,
            service_instance=service_instance,
            startup_policy=policy,
            datacenter_name="Datacenter",
            cluster_name="Cluster",
        )
        assert ret
        ret = esxi.list_services(
            service_name=SSH_SERVICE,
            service_instance=service_instance,
            datacenter_name="Datacenter",
            cluster_name="Cluster",
        )
        for host in ret:
            assert ret[host][SSH_SERVICE]["startup_policy"] == policy


def test_acceptance_level(service_instance):
    """
    Test acceptance level on esxi host
    """
    ret = esxi.set_acceptance_level(
        acceptance_level="community",
        service_instance=service_instance,
        datacenter_name="Datacenter",
        cluster_name="Cluster",
    )
    for h in ret:
        assert ret[h] == "community"

    ret = esxi.get_acceptance_level(
        acceptance_level="community",
        service_instance=service_instance,
        datacenter_name="Datacenter",
        cluster_name="Cluster",
    )
    assert set(ret.values()) == {"community"}


def test_advanced_config(service_instance):
    """
    Test advanced config on esxi host
    """
    ret = esxi.set_advanced_config(
        config_name="Annotations.WelcomeMessage",
        config_value="testing",
        service_instance=service_instance,
        datacenter_name="Datacenter",
        cluster_name="Cluster",
    )
    for h in ret:
        assert ret[h]["Annotations.WelcomeMessage"] == "testing"

    ret = esxi.get_advanced_config(
        config_name="Annotations.WelcomeMessage",
        service_instance=service_instance,
        datacenter_name="Datacenter",
        cluster_name="Cluster",
    )
    for h in ret:
        assert ret[h]["Annotations.WelcomeMessage"] == "testing"

    ret = esxi.set_advanced_configs(
        config_dict={"Annotations.WelcomeMessage": "test1", "BufferCache.FlushInterval": 3000},
        service_instance=service_instance,
        datacenter_name="Datacenter",
        cluster_name="Cluster",
    )
    for h in ret:
        assert ret[h]["Annotations.WelcomeMessage"] == "test1"
        assert ret[h]["BufferCache.FlushInterval"] == 3000

    ret = esxi.get_advanced_config(
        config_name="BufferCache.FlushInterval",
        service_instance=service_instance,
        datacenter_name="Datacenter",
        cluster_name="Cluster",
    )
    for h in ret:
        assert ret[h]["BufferCache.FlushInterval"] == 3000


def test_get_dns_config(service_instance):
    """
    Test get dns configuration on ESXi host
    """
    ret = esxi.get_dns_config(
        service_instance=service_instance,
        datacenter_name="Datacenter",
        cluster_name="Cluster",
    )
    assert ret
    for host in ret:
        assert ret[host]["ip"]
        assert ret[host]["host_name"]
        assert ret[host]["domain_name"]

    ret = esxi.get_dns_config(
        service_instance=service_instance,
        datacenter_name="Datacenter",
        cluster_name="Cluster",
        host_name="no_host",
    )
    assert not ret


def test_add(integration_test_config, service_instance):
    """
    Test esxi add
    """
    if integration_test_config["esxi_manage_test_instance"]:
        ret = esxi.add(
            integration_test_config["esxi_manage_test_instance"]["name"],
            integration_test_config["esxi_manage_test_instance"]["user"],
            integration_test_config["esxi_manage_test_instance"]["password"],
            integration_test_config["esxi_manage_test_instance"]["cluster"],
            integration_test_config["esxi_manage_test_instance"]["datacenter"],
            verify_host_cert=False,
            service_instance=service_instance,
        )
        assert ret["state"] == "connected"
    else:
        pytest.skip("test requires esxi manage test instance credentials")


def test_manage_disconnect(integration_test_config, service_instance):
    """
    Test esxi manage disconnect task
    """
    if integration_test_config["esxi_manage_test_instance"]:
        ret = esxi.disconnect(
            integration_test_config["esxi_manage_test_instance"]["name"],
            service_instance=service_instance,
        )
        assert ret["state"] == "disconnected"
    else:
        pytest.skip("test requires esxi manage test instance credentials")


def test_move(integration_test_config, service_instance):
    """
    Test esxi move
    """
    if integration_test_config["esxi_manage_test_instance"]:
        ret = esxi.move(
            integration_test_config["esxi_manage_test_instance"]["name"],
            integration_test_config["esxi_manage_test_instance"]["move"],
            service_instance=service_instance,
        )
        assert (
            ret["state"]
            == f"moved {integration_test_config['esxi_manage_test_instance']['name']} from {integration_test_config['esxi_manage_test_instance']['cluster']} to {integration_test_config['esxi_manage_test_instance']['move']}"
        )
    else:
        pytest.skip("test requires esxi manage test instance credentials")


def test_manage_connect(integration_test_config, service_instance):
    """
    Test esxi manage connect task
    """
    if integration_test_config["esxi_manage_test_instance"]:
        ret = esxi.connect(
            integration_test_config["esxi_manage_test_instance"]["name"],
            service_instance=service_instance,
        )
        assert ret["state"] == "connected"
    else:
        pytest.skip("test requires esxi manage test instance credentials")


def test_manage_remove(integration_test_config, service_instance):
    """
    Test esxi manage remove task
    """
    if integration_test_config["esxi_manage_test_instance"]:
        esxi.disconnect(
            integration_test_config["esxi_manage_test_instance"]["name"],
            service_instance=service_instance,
        )
        ret = esxi.remove(
            integration_test_config["esxi_manage_test_instance"]["name"],
            service_instance=service_instance,
        )
        assert (
            ret["state"]
            == f"removed host {integration_test_config['esxi_manage_test_instance']['name']}"
        )
    else:
        pytest.skip("test requires esxi manage test instance credentials")


def test_esxi_get(service_instance):
    """
    Test get configuration on ESXi host
    """
    ret = esxi.get(
        service_instance=service_instance,
        datacenter_name="Datacenter",
        cluster_name="Cluster",
    )
    assert ret
    for host in ret:
        assert ret[host]["cpu_model"]
        assert ret[host]["capabilities"]
        assert ret[host]["nics"]
        assert ret[host]["vsan"]
        assert ret[host]["datastores"]
        assert ret[host]["num_cpu_cores"]

    ret = esxi.get(
        service_instance=service_instance,
        datacenter_name="Datacenter",
        cluster_name="Cluster",
        key="vsan:health",
    )
    assert ret
    for host in ret:
        assert ret[host] == "unknown"

    ret = esxi.get(
        service_instance=service_instance,
        datacenter_name="Datacenter",
        cluster_name="Cluster",
        host_name="no_host",
    )
    assert not ret

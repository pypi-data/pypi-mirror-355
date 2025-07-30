import logging
import xml.dom.minidom
import xml.etree.ElementTree as ET
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

LOOPIA_API_URL = "https://api.loopia.se/RPCSERV"


def add_zone_record(
    username: str,
    password: str,
    domain: str,
    subdomain: str,
    record: "LoopiaApiRecordObj",
) -> None:
    request = (
        XmlRpcRequest("addZoneRecord")
        .add_param(username)
        .add_param(password)
        .add_param(domain)
        .add_param(subdomain)
        .add_param(record.as_dict())
    ).as_xml()

    response = requests.post(
        LOOPIA_API_URL,
        data=request,
        headers={"Content-Type": "text/xml"},
    )

    response_xml = ET.fromstring(response.text)

    logger.debug(
        "Add record response: %s",
        _pretty_print_xml_str(response.text) if response.text else "No response",
    )

    first_param = response_xml.find(".//param//value")
    if first_param is None or not first_param.findtext("string") == "OK":
        logger.error(
            f"Failed to add DNS record for {subdomain} in domain {domain}. "
            f"Response: {response.text}"
        )
        raise Exception(f"Failed to add DNS record for {subdomain} in domain {domain}.")


def find_zone_record_id(
    username: str,
    password: str,
    domain: str,
    subdomain: str,
    record_type: str,
    value: str,
) -> Optional[int]:
    records_request = (
        XmlRpcRequest("getZoneRecords")
        .add_param(username)
        .add_param(password)
        .add_param(domain)
        .add_param(subdomain)
    ).as_xml()

    response = requests.post(
        LOOPIA_API_URL,
        records_request,
        headers={"Content-Type": "text/xml"},
    )

    response_xml = ET.fromstring(response.text)
    return _find_record_id(response_xml, record_type, value)


def remove_zone_record(
    username: str,
    password: str,
    domain: str,
    subdomain: str,
    record_id: int,
) -> None:
    request = (
        XmlRpcRequest("removeZoneRecord")
        .add_param(username)
        .add_param(password)
        .add_param(domain)
        .add_param(subdomain)
        .add_param(record_id)
    )

    response = requests.post(
        LOOPIA_API_URL, request.as_xml(), headers={"Content-Type": "text/xml"}
    )

    logger.debug(
        "Delete record response: %s",
        _pretty_print_xml_str(response.text) if response.text else "No response",
    )


def _find_record_id(
    root: ET.Element,
    find_record_type: str,
    find_rdata: str,
) -> Optional[int]:
    for struct in root.findall(".//struct"):
        type_v = None
        data_v = None
        record_id_v = None
        for member in struct.findall("member"):
            name = member.find("name")
            value = member.find("value/*")
            if name is None or value is None:
                logger.warning(
                    f"Skipping struct with missing name or value. {name=}, {value=}"
                )
                continue

            if name.text == "type":
                type_v = value.text
            elif name.text == "rdata":
                data_v = value.text
            elif name.text == "record_id":
                record_id_v = int(value.text or 0)

        if type_v == find_record_type and data_v == find_rdata:
            logger.debug(
                f"Found matching record for cleanup: {type_v=}, {data_v=}, {record_id_v}"
            )
            return record_id_v
    return None


def _pretty_print_xml_str(xml_str: str | bytes) -> str:
    return xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ").strip()


class LoopiaApiRecordObj:
    def __init__(self, record_type: str, ttl: int, priority: int, data: str) -> None:
        self.record_type = record_type
        self.ttl = ttl
        self.priority = priority
        self.data = data

    def as_dict(self) -> dict[str, Any]:
        return {
            "type": self.record_type,
            "ttl": self.ttl,
            "priority": self.priority,
            "rdata": self.data,
        }


class XmlRpcRequest:
    def __init__(self, method: str) -> None:
        self.method = method
        self.params: list[Any] = []

    def add_param(self, value: Any) -> "XmlRpcRequest":
        self.params.append(value)
        return self

    def as_xml(self) -> str:
        root = ET.Element("methodCall")
        ET.SubElement(root, "methodName").text = self.method
        params = ET.SubElement(root, "params")
        for param in self.params:
            param_e = ET.SubElement(params, "param")
            self._create_value_element(param_e, param)

        return _pretty_print_xml_str(ET.tostring(root))

    def _create_value_element(self, parent: ET.Element, value: Any) -> None:
        value_e = ET.SubElement(parent, "value")

        match value:
            case str():
                ET.SubElement(value_e, "string").text = value
            case int():
                ET.SubElement(value_e, "int").text = str(value)
            case float():
                ET.SubElement(value_e, "double").text = str(value)
            case bool():
                ET.SubElement(value_e, "boolean").text = "1" if value else "0"
            case dict():
                struct_e = ET.SubElement(value_e, "struct")
                for k, v in value.items():  # type: ignore
                    member_e = ET.SubElement(struct_e, "member")
                    ET.SubElement(member_e, "name").text = str(k)  # type: ignore
                    self._create_value_element(member_e, v)
            case _:
                raise ValueError(f"Unsupported type for XML-RPC value: {type(value)}")

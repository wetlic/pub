import textfsm


def __parse_with_template(raw_output, template_filename, relative_path=None):
    # prevent errors when using this method as a submodule
    if relative_path is not None:
        template_filename = relative_path + template_filename

    # parse
    parsed_output = []
    with open(template_filename, "r") as template:
        re_table = textfsm.TextFSM(template)
        parsed_output.append(re_table.header)
        parsed_output += re_table.ParseText(raw_output)
    return parsed_output


# ---------- IOS-XE


def parse_iosxe_show_ntp_associations(raw_output, relative_path=None):
    """
    parse output from "show ntp assosications", works with IOS, IOS-XE and ASA
    :param raw_output: string
    :param relative_path: string with path to the git repository, e.g. python_network_tools/
    :rtype: list of lists, first element is field desription
    """
    # for this limited funcionality the same template can be used for IOS and IOS-XE
    return __parse_with_template(raw_output, "parser_templates/iosxe_show_ntp_associations.textfsm", relative_path)


# ---------- NXOS


def parse_nxos_show_ntp_peer_status(raw_output, relative_path=None):
    """
    parse output from "show ntp peer-status", works with NXOS
    :param raw_output: string
    :param relative_path: string with path to the git repository, e.g. python_network_tools/
    :rtype: list of lists, first element is field desription
    """
    return __parse_with_template(raw_output, "parser_templates/nxos_show_ntp_peer_status.textfsm", relative_path)


# ---------- Procurve


def parse_procurve_show_sntp(raw_output, relative_path=None):
    """
    parse output from "show sntp", works with Procurve
    :param raw_output: string
    :param relative_path: string with path to the git repository, e.g. python_network_tools/
    :rtype: list of lists, first element is field desription
    """
    return __parse_with_template(raw_output, "parser_templates/procurve_show_sntp.textfsm", relative_path)

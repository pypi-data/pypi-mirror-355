import requests
import json
import logging
import re
import importlib.util
import os
import pprint
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RETIREJS_URL = "https://raw.githubusercontent.com/RetireJS/retire.js/master/repository/jsrepository.json"
VERSION_PLACEHOLDER_REGEX = r"§§version§§"
VERSION_REPLACEMENT_REGEX = r"[0-9][0-9.a-z_-]+"
DEFAULT_VULNERABILITIES_FILEPATH = "retirejs/vulnerabilities.py"

# Define expected fields to check for potential breaking changes or missing critical data
CRITICAL_COMPONENT_FIELDS = {"vulnerabilities", "extractors"}
KNOWN_COMPONENT_FIELDS = {"bowername", "npmname", "basePurl", "vulnerabilities", "extractors", "comment", "github"}
KNOWN_VULNERABILITY_FIELDS = {"below", "atOrAbove", "severity", "info", "identifiers", "cwe"}
KNOWN_IDENTIFIER_FIELDS = {"summary", "bug", "issue", "release", "osvdb", "CVE", "retid", "githubID", "PR", "gist", "blog", "tenable"}
KNOWN_EXTRACTOR_FIELDS = {"func", "hashes", "filename", "filecontent", "uri", "filecontentreplace"}


def fetch_retirejs_data():
    """
    Fetches vulnerability data from the RetireJS repository.
    """
    logging.info(f"Fetching RetireJS data from: {RETIREJS_URL}")
    try:
        response = requests.get(RETIREJS_URL)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data from {RETIREJS_URL}: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON data from {RETIREJS_URL}: {e}")
        return None

def load_existing_vulnerabilities(filepath=DEFAULT_VULNERABILITIES_FILEPATH):
    """
    Loads the existing 'definitions' dictionary from the given Python file.
    """
    if not os.path.exists(filepath):
        logging.warning(f"Vulnerability file '{filepath}' not found. Returning empty definitions.")
        return {}
    logging.info(f"Loading existing vulnerabilities from: {filepath}")
    try:
        spec = importlib.util.spec_from_file_location("vulnerabilities", filepath)
        if spec is None or spec.loader is None:
            logging.error(f"Could not create module spec from '{filepath}'.")
            return {}
        vulnerabilities_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vulnerabilities_module)

        if hasattr(vulnerabilities_module, 'definitions'):
            return json.loads(json.dumps(getattr(vulnerabilities_module, 'definitions')))
        else:
            logging.warning(f"'definitions' dictionary not found in '{filepath}'. Returning empty definitions.")
            return {}
    except Exception as e:
        logging.error(f"Error loading existing vulnerabilities from '{filepath}': {e}")
        return {}

def write_updated_vulnerabilities(definitions_to_write, filepath=DEFAULT_VULNERABILITIES_FILEPATH):
    """
    Writes the given definitions dictionary to the specified Python file.
    """
    logging.info(f"Starting to write updated definitions to '{filepath}'...")
    try:
        with open(filepath, 'w') as f:
            f.write("definitions = ")
            # f.write(pprint.pformat(definitions_to_write, indent=4, width=120))
            f.write(json.dumps(definitions_to_write, indent=4, sort_keys=True))
            f.write("\n")
        logging.info(f"Successfully wrote updated definitions to '{filepath}'.")
    except IOError as e:
        logging.error(f"Error writing definitions to '{filepath}': {e}")

def transform_vulnerabilities(retirejs_vulnerabilities, component_name):
    transformed_vulnerabilities = []
    if not isinstance(retirejs_vulnerabilities, list):
        logging.warning(f"Component '{component_name}': Expected list for vulnerabilities, got {type(retirejs_vulnerabilities)}. Skipping vulnerabilities transformation for this component.")
        return []

    for vuln_idx, vuln in enumerate(retirejs_vulnerabilities):
        if not isinstance(vuln, dict):
            logging.warning(f"Component '{component_name}', vulnerability index {vuln_idx}: Expected dict, got {type(vuln)}. Skipping this vulnerability.")
            continue
        new_vuln = {}

        for field in KNOWN_VULNERABILITY_FIELDS:
            if field in vuln:
                if field == "info" and isinstance(vuln[field], list):
                     new_vuln[field] = sorted(list(set(vuln[field])))
                else:
                    new_vuln[field] = vuln[field]

        if "identifiers" in vuln:
            if isinstance(vuln["identifiers"], dict):
                new_identifiers = {}
                for k, v in vuln["identifiers"].items():
                    if k == "CVE":
                        new_identifiers["CVE"] = sorted(list(set([v] if isinstance(v, str) else v)))
                    elif k in KNOWN_IDENTIFIER_FIELDS:
                        new_identifiers[k] = v
                    else:
                        logging.info(f"Component '{component_name}', vulnerability {vuln.get('identifiers', {}).get('summary', vuln_idx)}: New identifier field '{k}' with value '{v}'.")
                        new_identifiers[k] = v
                new_vuln["identifiers"] = new_identifiers
                for id_field in vuln["identifiers"]:
                    if id_field not in KNOWN_IDENTIFIER_FIELDS and id_field not in new_identifiers: # Already logged and added
                        logging.info(f"Component '{component_name}', vulnerability {vuln.get('identifiers', {}).get('summary', vuln_idx)}: Unexpected field '{id_field}' in identifiers.")
            else:
                logging.warning(f"Component '{component_name}', vulnerability {vuln.get('identifiers', {}).get('summary', vuln_idx)}: Expected dict for identifiers, got {type(vuln['identifiers'])}.")

        transformed_vulnerabilities.append(new_vuln)

        # Preserve any unexpected fields at the vulnerability level
        for field in vuln:
            if field not in new_vuln: # If not already processed (i.e. it's not a known field or part of identifiers)
                if field not in KNOWN_VULNERABILITY_FIELDS: # Log only if truly unexpected based on our known list
                    logging.info(f"Component '{component_name}', vulnerability {vuln.get('identifiers', {}).get('summary', vuln_idx)}: Unexpected field '{field}' with value '{vuln[field]}'. Adding as is.")
                new_vuln[field] = vuln[field] # Add it to the transformed vulnerability

    return transformed_vulnerabilities

def transform_extractors(retirejs_extractors, component_name):
    if not isinstance(retirejs_extractors, dict):
        logging.warning(f"Component '{component_name}': Expected dict for extractors, got {type(retirejs_extractors)}. Skipping extractors transformation.")
        return {}

    new_extractors = {}
    for field in KNOWN_EXTRACTOR_FIELDS:
        if field in retirejs_extractors:
            if field in ["filename", "filecontent", "uri"]:
                new_extractors[field] = sorted(list(set([
                    re.sub(VERSION_PLACEHOLDER_REGEX, VERSION_REPLACEMENT_REGEX, regex_str)
                    for regex_str in retirejs_extractors[field]
                ])))
            elif field == "filecontentreplace":
                new_filecontentreplace = []
                for item in retirejs_extractors[field]:
                    if not item or len(item) < 3: # Need at least 3 chars for something like /a/b
                        logging.warning(f"Component '{component_name}': filecontentreplace item '{item}' is too short or empty. Keeping original.")
                        new_filecontentreplace.append(item)
                        continue

                    delimiter = item[0]
                    # Ensure the item is actually using this delimiter format, e.g., /regex/replace/flags
                    # We expect at least two delimiters for a valid pattern and replacement part.
                    split_parts = item[1:].split(delimiter)

                    if len(split_parts) >= 2: # We have at least "regex" and "replacement" parts
                        regex_pattern_part = split_parts[0]
                        replacement_part = split_parts[1]
                        flags_part = delimiter.join(split_parts[2:]) if len(split_parts) > 2 else ""

                        modified_regex_pattern_part = re.sub(VERSION_PLACEHOLDER_REGEX, VERSION_REPLACEMENT_REGEX, regex_pattern_part)

                        # Base reconstruction (delimiter + regex + delimiter + replacement)
                        reconstructed_item = f"{delimiter}{modified_regex_pattern_part}{delimiter}{replacement_part}"

                        # Add flags if they exist (i.e., if there was a third delimiter segment or more)
                        if len(split_parts) > 2:
                            all_flags_str = delimiter.join(split_parts[2:]) # this joins all remaining parts with the delimiter
                            reconstructed_item += f"{delimiter}{all_flags_str}"
                        # If the original item ended with a delimiter and the reconstructed one doesn't, add it.
                        # This covers cases like "/pattern/replacement/" where flags_part would be empty.
                        elif item.endswith(delimiter) and not reconstructed_item.endswith(delimiter):
                             reconstructed_item += delimiter

                        new_filecontentreplace.append(reconstructed_item)
                    else:
                        logging.warning(f"Component '{component_name}': Unexpected format for filecontentreplace item '{item}'. Could not split into regex/replacement. Keeping original.")
                        new_filecontentreplace.append(item)
                new_extractors[field] = sorted(list(set(new_filecontentreplace)))
            elif field == "func" or field == "hashes": # Direct mapping for func and hashes
                new_extractors[field] = retirejs_extractors[field]
            # No else needed here, if a KNOWN_EXTRACTOR_FIELD is not in retirejs_extractors, it's skipped as intended.

    for field in retirejs_extractors:
        if field not in new_extractors: # If not processed by the loop above (i.e. it's an unknown field)
            logging.info(f"Component '{component_name}': New/unexpected extractor type '{field}'. Adding as is.")
            new_extractors[field] = retirejs_extractors[field]
    return new_extractors

def transform_component_data(component_name, component_data_from_retirejs):
    logging.debug(f"Starting transformation for component: {component_name}")
    new_component_data = {}

    for field in CRITICAL_COMPONENT_FIELDS:
        if field not in component_data_from_retirejs:
            logging.warning(f"Component '{component_name}': Critical field '{field}' is missing from RetireJS data. This might indicate a breaking change or incomplete data.")

    for field in KNOWN_COMPONENT_FIELDS:
        if field in component_data_from_retirejs:
            if field == "bowername":
                bowernames = component_data_from_retirejs[field]
                if isinstance(bowernames, str):
                    new_component_data[field] = sorted(list(set([bowernames])))
                elif isinstance(bowernames, list):
                    new_component_data[field] = sorted(list(set(bowernames)))
                else:
                    logging.warning(f"Component '{component_name}': Unexpected type for bowername: {type(bowernames)}. Skipping.")
            elif field == "vulnerabilities":
                new_component_data[field] = transform_vulnerabilities(
                    component_data_from_retirejs.get(field, []), component_name
                )
            elif field == "extractors":
                new_component_data[field] = transform_extractors(
                    component_data_from_retirejs.get(field, {}), component_name
                )
            else:
                 new_component_data[field] = component_data_from_retirejs[field]
        elif field in CRITICAL_COMPONENT_FIELDS: # Already logged above, but ensure they are present in output structure
             new_component_data[field] = {} if field == "extractors" else []


    for field in component_data_from_retirejs:
        if field not in KNOWN_COMPONENT_FIELDS and field not in new_component_data:
            logging.info(f"Component '{component_name}': New/unexpected top-level field '{field}'. Adding as is. Value: {component_data_from_retirejs[field]}")
            new_component_data[field] = component_data_from_retirejs[field]

    # Ensure critical fields always exist in the output, even if empty and not in source
    if "vulnerabilities" not in new_component_data:
        new_component_data["vulnerabilities"] = []
    if "extractors" not in new_component_data:
        new_component_data["extractors"] = {}

    return new_component_data

def handle_deleted_vulnerabilities(existing_definitions, new_definitions):
    """
    Handles vulnerabilities that were deleted in the source repository.
    Returns a dictionary of components that were deleted and should be removed.
    """
    deleted_components = {}
    for component_name, component_data in existing_definitions.items():
        if component_name not in new_definitions:
            logging.info(f"Component '{component_name}' was deleted in the source repository.")
            deleted_components[component_name] = component_data
    return deleted_components

def validate_transformed_data(transformed_data, component_name):
    """
    Validates the transformed data to ensure it meets our requirements.
    Returns True if valid, False otherwise.
    """
    if not isinstance(transformed_data, dict):
        logging.error(f"Component '{component_name}': Transformed data is not a dictionary")
        return False
    
    # Check for required fields
    if "vulnerabilities" not in transformed_data:
        logging.error(f"Component '{component_name}': Missing required field 'vulnerabilities'")
        return False
    
    if "extractors" not in transformed_data:
        logging.error(f"Component '{component_name}': Missing required field 'extractors'")
        return False
    
    # Validate vulnerabilities
    if not isinstance(transformed_data["vulnerabilities"], list):
        logging.error(f"Component '{component_name}': Vulnerabilities must be a list")
        return False
    
    # Validate extractors
    if not isinstance(transformed_data["extractors"], dict):
        logging.error(f"Component '{component_name}': Extractors must be a dictionary")
        return False
    
    return True

def normalize_component(component):
    """
    Normalizes a component's data structure to ensure consistent comparison.
    """
    normalized = {}
    
    # Sort vulnerabilities by their identifiers to ensure consistent ordering
    if "vulnerabilities" in component:
        normalized["vulnerabilities"] = sorted(
            component["vulnerabilities"],
            key=lambda x: json.dumps(x.get("identifiers", {}), sort_keys=True)
        )
    
    # Sort extractors
    if "extractors" in component:
        normalized["extractors"] = {
            k: sorted(v) if isinstance(v, list) else v
            for k, v in sorted(component["extractors"].items())
        }
    
    # Sort other fields
    for field in sorted(component.keys()):
        if field not in ["vulnerabilities", "extractors"]:
            if isinstance(component[field], list):
                normalized[field] = sorted(component[field])
            else:
                normalized[field] = component[field]
    
    return normalized

def are_definitions_different(old_definitions, new_definitions):
    """
    Compares old and new definitions to detect if there are actual changes.
    Returns True if there are changes, False otherwise.
    """
    if set(old_definitions.keys()) != set(new_definitions.keys()):
        return True
    
    for component_name in new_definitions:
        old_component = normalize_component(old_definitions.get(component_name, {}))
        new_component = normalize_component(new_definitions[component_name])
        
        if old_component != new_component:
            return True
    
    return False

if __name__ == "__main__":
    start_time = datetime.datetime.now()
    logging.info(f"Update script started at: {start_time.isoformat()}")

    existing_definitions = load_existing_vulnerabilities()
    logging.info(f"Loaded {len(existing_definitions)} existing components.")

    fetched_data = fetch_retirejs_data()

    if fetched_data:
        actual_components_from_fetch = fetched_data
        logging.info(f"Successfully fetched {len(actual_components_from_fetch)} remote components from RetireJS.")

        new_definitions = {}
        validation_errors = []
        for component_name, component_data in actual_components_from_fetch.items():
            if not isinstance(component_data, dict):
                validation_errors.append(f"Component '{component_name}' data is not a dictionary (type: {type(component_data)})")
                continue
            transformed_data = transform_component_data(component_name, component_data)
            
            # Validate transformed data
            if not validate_transformed_data(transformed_data, component_name):
                validation_errors.append(f"Component '{component_name}' failed validation")
                continue
                
            new_definitions[component_name] = transformed_data

        if validation_errors:
            error_msg = "Validation errors occurred:\n" + "\n".join(validation_errors)
            logging.error(error_msg)
            raise ValueError(error_msg)

        logging.info(f"Successfully transformed {len(new_definitions)} new/updated components from fetched data.")

        # Handle deleted vulnerabilities
        deleted_components = handle_deleted_vulnerabilities(existing_definitions, new_definitions)
        
        # Summary of changes
        existing_keys = set(existing_definitions.keys())
        new_keys = set(new_definitions.keys())
        deleted_keys = set(deleted_components.keys())

        added_components = sorted(list(new_keys - existing_keys))
        # Only include components that actually changed
        updated_components = sorted([
            component_name for component_name in (new_keys & existing_keys)
            if normalize_component(existing_definitions[component_name]) != normalize_component(new_definitions[component_name])
        ])
        removed_components = sorted(list(deleted_keys))

        logging.info(f"--- Summary of Changes ---")
        logging.info(f"Components added: {len(added_components)}")
        if added_components:
            logging.info(f"Added component names: {', '.join(added_components)}")

        logging.info(f"Components updated: {len(updated_components)}")
        if updated_components:
            logging.info(f"Updated component names: {', '.join(updated_components)}")

        logging.info(f"Components removed: {len(removed_components)}")
        if removed_components:
            logging.info(f"Removed component names: {', '.join(removed_components)}")

        # Merge definitions - only keep components that are in new_definitions
        merged_definitions = new_definitions.copy()

        logging.info(f"Total components in existing definitions: {len(existing_keys)}")
        logging.info(f"Total components from fetched data: {len(new_keys)}")
        logging.info(f"Total components after merging: {len(merged_definitions)}")

        # Count total vulnerabilities before and after
        total_vulns_before = sum(len(comp.get('vulnerabilities', [])) for comp in existing_definitions.values())
        total_vulns_after = sum(len(comp.get('vulnerabilities', [])) for comp in merged_definitions.values())
        logging.info(f"Total vulnerabilities before: {total_vulns_before}")
        logging.info(f"Total vulnerabilities after: {total_vulns_after}")
        if total_vulns_after != total_vulns_before:
            logging.info(f"Net change in vulnerabilities: {total_vulns_after - total_vulns_before}")

        if merged_definitions:
            # Check if there are actual changes before writing
            if are_definitions_different(existing_definitions, merged_definitions):
                write_updated_vulnerabilities(merged_definitions)
                logging.info(f"The '{DEFAULT_VULNERABILITIES_FILEPATH}' file has been updated with the latest definitions.")
            else:
                logging.info("No changes detected in the vulnerability data. Skipping file update.")

    else:
        logging.error("Failed to fetch data from RetireJS. No transformation, merge, or write performed.")

    end_time = datetime.datetime.now()
    logging.info(f"Update script finished at: {end_time.isoformat()}")
    logging.info(f"Total execution time: {end_time - start_time}")

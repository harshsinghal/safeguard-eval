"""Provisional, multi-label ontology; types are hypotheses, not discovered truths."""
MODEL='fastino/gliner2.5-multi-v1'
REVISION='7b005274e82da37dcf1f5fd9d6a2ef413c6a004c'
ENTITY_TYPES={
 'person':'A named person or a specific person described by a role or relationship.',
 'identity_group':'A group identified by race, ethnicity, nationality, religion, gender, sexuality or disability.',
 'organization_or_account':'An organization, institution, business, government body, user account or financial account.',
 'personal_or_private_information':'Personal details, private messages, call history, address, recordings or confidential records.',
 'authentication_material':'Password, API key, access token, JWT, SSH key, secret key or wallet credential.',
 'computing_resource':'A file, directory, database, host, server, network, domain, process or environment setting.',
 'software_artifact':'Code, script, program, malware, software package, agent skill or configuration artifact.',
 'tool_or_external_service':'A callable tool, API, application, messaging service, cloud service or publishing platform.',
 'instruction_or_policy':'System prompt, prior instruction, rule, policy, command or claimed authority statement.',
 'content_artifact_or_symbol':'Post, story, image description, document, message, fictional character or symbolic religious imagery.',
 'animal_or_physical_subject':'An animal, body part or physical object affected by an action.',
 'health_or_substance':'A medicine, drug, health condition, medical treatment, injury or self-harm subject.',
}
ACTION_TYPES={
 'read_or_retrieve':'Read, search, inspect, find, obtain or retrieve information.',
 'generate_or_transform':'Write, generate, summarize, translate, explain or transform content.',
 'execute_or_modify':'Run, execute, install, configure, change or update something.',
 'delete_or_disrupt':'Delete, destroy, disable, encrypt, interrupt or disrupt.',
 'transmit_or_publish':'Send, upload, disclose, distribute, publish or transfer.',
 'authenticate_or_access':'Authenticate, log in, grant access, access a resource or change permissions.',
 'override_or_redirect':'Override instructions, ignore rules, redirect the task or impersonate authority.',
 'persuade_or_target':'Persuade, impersonate, harass, stereotype, incite or target someone.',
 'physical_intervention':'Treat, administer, train, injure or otherwise physically act on a living subject.',
}
FRAME_FIELDS={
 'actor':'Who is requested or described to act. Extract explicit text only.',
 'action':'The requested or described action phrase. Extract explicit text only.',
 'target':'What or whom the action affects. Extract explicit text only.',
 'claimed_purpose':'A stated purpose or justification. Do not infer an unstated intent.',
 'claimed_authorization':'Explicit permission or claimed authority. A claim is not verified authorization.',
}
THRESHOLDS=(.35,.50,.65)


ACTION_LABELS=dict(zip(ACTION_TYPES, ['information retrieval','content generation','execution or configuration','deletion or disruption','transmission or publishing','authentication or resource access','instruction override','persuasion or targeting','physical intervention']))


def build_schema():
    from gliner2 import Schema
    builder=(Schema().entities(ENTITY_TYPES)
        .classification('action_types',{ACTION_LABELS[k]:v for k,v in ACTION_TYPES.items()},multi_label=True,cls_threshold=.35)
        .structure('action_frame'))
    for k,v in FRAME_FIELDS.items():builder=builder.field(k,dtype='str',description=v)
    return builder.build()

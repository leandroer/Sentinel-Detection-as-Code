param environment string
param location string
param workspaceName string

var evidenceName = 'logic-sentinel-evidence-${environment}'
var containmentName = 'logic-sentinel-containment-${environment}'

resource evidence 'Microsoft.Logic/workflows@2019-05-01' = {
  name: evidenceName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    state: 'Enabled'
    definition: {
      '$schema': 'https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#'
      contentVersion: '1.0.0.0'
      parameters: {}
      triggers: {
        sentinel_incident: {
          type: 'Request'
          kind: 'Http'
          inputs: {
            schema: {
              type: 'object'
            }
          }
        }
      }
      actions: {
        compose_evidence_record: {
          type: 'Compose'
          inputs: {
            workspace: workspaceName
            environment: environment
            incident: '@triggerBody()'
            collectedAt: '@utcNow()'
            mode: 'simulation'
          }
        }
      }
      outputs: {}
    }
  }
}

resource containment 'Microsoft.Logic/workflows@2019-05-01' = {
  name: containmentName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    state: 'Enabled'
    definition: {
      '$schema': 'https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#'
      contentVersion: '1.0.0.0'
      parameters: {}
      triggers: {
        sentinel_incident: {
          type: 'Request'
          kind: 'Http'
          inputs: {
            schema: {
              type: 'object'
            }
          }
        }
      }
      actions: {
        compose_containment_plan: {
          type: 'Compose'
          inputs: {
            environment: environment
            requestedAt: '@utcNow()'
            mode: 'simulation'
            message: 'Containment requires analyst approval and a separately authorized connector.'
            incident: '@triggerBody()'
          }
        }
      }
      outputs: {}
    }
  }
}

output evidencePlaybookName string = evidence.name
output containmentPlaybookName string = containment.name

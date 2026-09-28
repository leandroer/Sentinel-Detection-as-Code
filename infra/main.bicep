targetScope = 'resourceGroup'

@allowed(['dev', 'test', 'prod'])
param environment string = 'dev'
param location string = resourceGroup().location
param workspaceName string = 'law-sentinel-detection-${environment}'
param retentionInDays int = environment == 'prod' ? 90 : 30

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  properties: {
    retentionInDays: retentionInDays
    sku: {
      name: 'PerGB2018'
    }
  }
}

resource sentinel 'Microsoft.OperationsManagement/solutions@2015-11-01-preview' = {
  name: 'SecurityInsights(${workspace.name})'
  location: location
  plan: {
    name: 'SecurityInsights(${workspace.name})'
    product: 'OMSGallery/SecurityInsights'
    publisher: 'Microsoft'
    promotionCode: ''
  }
  properties: {
    workspaceResourceId: workspace.id
  }
}

module responsePlaybooks 'modules/response-playbooks.bicep' = {
  name: 'response-playbooks'
  params: {
    environment: environment
    location: location
    workspaceName: workspace.name
  }
}

output workspaceName string = workspace.name
output workspaceId string = workspace.id
output evidencePlaybookName string = responsePlaybooks.outputs.evidencePlaybookName
output containmentPlaybookName string = responsePlaybooks.outputs.containmentPlaybookName

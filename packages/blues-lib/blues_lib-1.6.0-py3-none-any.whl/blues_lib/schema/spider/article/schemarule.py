schemarule = {
  "type": "object", 
  "properties": {

    "browser": {
      "type": "object",
      "properties": {
        "mode": {
          "type": "string", 
          "enum":["standard","headless","headlesslogin","debug","login","proxy","remote"] 
        }, 
        "path": {
          "type": "string", 
          "enum":["config","env","manager"] 
        },
      },
      "required": ["mode","path"]
    },

    "basic": {
      "type": "object",
      "properties": {
        "mode":{
          "type": "string",
          "enum":["article","gallery"] 
        },
        "artifact":{
          "type": "string",
          "enum":["briefs","material","materials"] 
        },
        "site":{
          "type": "string",
          "not": { "pattern": "^$" },
        },
        "lang":{
          "type": "string",
          "enum":["cn","en"] 
        },
        "brief_url": {
          "type": "string",
          "format": "url",
          "not": { "pattern": "^$" },
        }, 
        "persistent":{
          "type": "boolean",
        },
      },
      "required": ["mode","site","lang","brief_url","persistent"]
    },

    "limit": {
      "type": "object",
      "properties": {
        "max_material_count":{
          "type": "integer",
          "minimum":1,
          "maximum":100,
        },
        "max_material_image_count": {
          "type": "integer",
          "minimum":1,
          "maximum":50,
        }, 
        "min_content_length": {
          "type": "integer",
          "minimum":100,
          "maximum":500,
        }, 
        "max_content_length": {
          "type": "integer",
          "minimum":500,
          "maximum":8000,
        }, 
      },
      "required": ["max_material_image_count","min_content_length","max_content_length"]
    },

    "brief_preparation":{
      "type": ["object","null"],
    },

    "brief_execution":{
      "type": ["object","null"],
    },

    "brief_cleanup":{
      "type": ["object","null"],
    },

    "material_preparation":{
      "type": ["object","null"],
    },

    "material_execution":{
      "type": ["object","null"],
    },

    "material_cleanup":{
      "type": ["object","null"],
    },
  },

  "required": ["browser","basic","brief_preparation","brief_execution","brief_cleanup","material_preparation","material_execution","material_cleanup"],
}
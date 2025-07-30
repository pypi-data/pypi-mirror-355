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
          "enum":["article","gallery","video"] 
        },
        "site":{
          "type": "string",
          "not": { "pattern": "^$" },
        },
        "url": {
          "type": "string",
          "format": "url",
          "not": { "pattern": "^$" },
        }, 
        "field":{
          "type": "string",
          "enum":["raw","ai"] 
        },
        "preview":{
          "type": "boolean",
        },
      },
      "required": ["mode","site","url","preview"]
    },
    
    "limit": {
      "type": "object",
      "properties": {
        "title_max_length":{
          "type": "integer",
          "minimum":1,
          "maximum":50,
        },
        "content_max_length": {
          "type": "integer",
          "minimum":1,
          "maximum":5000,
        }, 
        "image_max_length": {
          "type": "integer",
          "minimum":0,
          "maximum":20,
        }, 
      },
      "required": ["title_max_length","content_max_length","image_max_length"]
    },

    "preparation":{
      "type": ["object","null"],
    },

    "title_execution":{
      "type": ["object"],
    },

    "outhers_execution" :{
      "type": ["object","null"],
    },

    "thumbnail_execution":{
      "type": ["object"],
    },

    "content_execution":{
      "type": ["object"],
    },

    "preview_execution":{
      "type": ["object","null"],
    },

    "submit_execution":{
      "type": ["object"],
    },

    "cleanup":{
      "type": ["object","null"],
    },
  },

  "required": ["browser","basic","limit","preparation","title_execution","thumbnail_execution","content_execution","preview_execution","submit_execution","cleanup"],
}
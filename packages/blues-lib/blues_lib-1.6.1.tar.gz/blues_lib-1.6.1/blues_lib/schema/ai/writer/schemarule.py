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
          "enum":["writer","gallery","video"] 
        },
        "site":{
          "type": "string",
          "not": { "pattern": "^$" },
        },
        "url": {
          "type": "string",
          "format": "url",
          "not": { "pattern": "^$" },
        } 
      },
      "required": ["mode","site","url"]
    },

    "material": {
      "type": "object",
      "properties": {
        "mode":{
          "type": "string",
          "enum":["article","gallery","video"] 
        },
      },
      "required": ["mode"]
    },

    "preparation":{
      "type": ["object","null"],
    },

    "execution":{
      "type": ["object"],
    },

    "cleanup":{
      "type": ["object","null"],
    },
  },

  "required": ["browser","basic","preparation","execution","cleanup"],
}
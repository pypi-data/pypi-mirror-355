from mcp_purchase.databases import *
import mcp.types as types



# MongoDB tool definitions for mcp_purchase

mongodb_tools = [
    types.Tool(
        name="get_budget_expense_table_schema",
        description="This tool retrieves Typesense schema and instructions on how to query a typesense table for a specific category.",
        inputSchema={
            "type": "object",
            "required": ["category"],
            "properties": {
                "category": {
                    "type": "string",
                    "description": "The category for which to retrieve the Typesense schema",
                    "enum": ["budget","expense"]
                }
            }            
        }
    ),
    types.Tool(
        name="smart_purchase_table_search",
        description= "Universal search tool for vessel purchase requisitions, purchase orders, invoices, and procurement data. Primary tool for querying purchase data across the fleet including requisitions, orders, suppliers, and financial information. Handles everything from specific order lookups to procurement tracking and budget management.",
        inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language or keyword query. This is matched against the fields purchaseRequisitionNumber, prDescription, purchaseRequisitionSummary, qtcNo and purchaseOrderNumber. Use '*' to match all records.",
                "default": "*"
            },
            "filters": {
                "type": "object",
                "description": "Optional filters to narrow the search results. Only use this if exact field values are known.",
                "properties": {
                    "imo": {
                        "type": "number",
                        "description": "IMO number of the vessel"
                    },
                    "vesselName": {
                        "type": "string",
                        "description": "Exact or partial name of the vessel"
                    },
                    "purchaseRequisitionNumber": {
                        "type": "string",
                        "description": "Unique purchase requisition (PR) number"
                    },
                    "purchaseOrderNumber": {
                        "type": "string",
                        "description": "Unique purchase order (PO) number"
                    },
                    "purchaseRequisitionStatus": {
                        "type": "string",
                        "description": "Status of the purchase requisition",
                        "enum": ["DRAFT", "APPROVED", "SENT FOR QUOTE", "AWAITING APPROVAL", "QUOTED", "PO APPROVED", "PO GENERATED", "ORDERED", "CLOSED", "CANCELLED", "PARTIALLY RECEIVED", "UNDER AMENDMENT"]
                    },
                    "purchaseOrderStatus": {
                        "type": "string",
                        "description": "Status of the purchase order",
                        "enum": ["CLOSED", "WITH FORWARDER", "CANCELLED", "ORDERED", "AWAITING APPROVAL", "UNDER AMENDMENT", "APPROVED", "DRAFT", "REJECTED", "QUOTED"]
                    },
                    "invoiceStatus": {
                        "type": "string",
                        "description": "Status of the invoice",
                        "enum": ["TRANSFERRED", "WAITING", "REJECTED", "READYFORTRANSFER", "NEW", "ONHOLD", "NOT RECEIVED"]
                    },
                    "purchaseOrderStage": {
                        "type": "string",
                        "description": "Indicates whether a purchase order is open or closed",
                        "enum": ["OPEN", "CLOSE"]
                    },
                    "purchaseRequisitionType": {
                        "type": "string",
                        "description": "Category/type of the purchase requisition",
                        "enum": ["ANTI-PIRACY ITEMS", "CHARTS PUBLICATIONS", "FLAG LOG BOOKS", "FUEL ADDITIVES", "GAS MEASUREMENT EQUIPMENTS", "GASES WELDING", "GENERAL STORES", "LICENSE", "LSA-FFA", "LUBE OILS GREASES", "MAINTENANCE CHEMICALS", "PAINTS THINNERS", "SYNERGY PPE KIT", "PERSONNEL PROTECTION", "SAFETY", "SCRUBBER BWTS CHEMICALS", "MARPOL SEALS", "SERVICE", "SPARE PARTS", "PRINTED STATIONARY KITS", "STORE", "TANK/HOLD CLEANING CHEMICALS"]
                    },
                    "orderPriority": {
                        "type": "string",
                        "description": "Priority level of the purchase requisition or order",
                        "enum": ["DEFECT", "ROUTINE MAINTENANCE STOCK", "NORMAL", "RECOMMENDED STOCK", "URGENT", "OTHERS", "DRY DOCK", "AUDIT"]
                    },
                    "vendorOrsupplierName": {
                        "type": "string",
                        "description": "Name of the supplier or vendor"
                    },
                    "forwarderName": {
                        "type": "string",
                        "description": "Name of the logistics forwarder",
                        "enum": ["AQUARIUS", "MARINE TRANS", "ONE LOOP"]
                    },
                    "currencyCode": {
                        "type": "string",
                        "description": "Currency code (e.g., USD, SGD, EUR)"
                    },
                    "orderType": {
                        "type": "string",
                        "description": "Type of purchase order",
                        "enum": ["OL", "OF"]
                    },
                    "cargoType": {
                        "type": "string",
                        "description": "Type of cargo for the purchase order",
                        "enum": ["DG", "NORMAL"]
                    },
                    "accountCode": {
                        "type": "string",
                        "description": "Account code under which the requisition is raised"
                    },
                    "poCreatedBy": {
                        "type": "string",
                        "description": "Name of the person who created the purchase order"
                    },
                    "invoiceApproverName": {
                        "type": "string",
                        "description": "Name of the person who approved the invoice"
                    },
                    "directPo": {
                        "type": "boolean",
                        "description": "Indicates whether the purchase order is a Direct PO"
                    },
                    "poInvoiceDiscrepency": {
                        "type": "boolean",
                        "description": "Indicates if there's a discrepancy between PO and invoice amounts"
                    },
                    "isNewPurchaseRequisition": {
                        "type": "boolean",
                        "description": "Indicates whether the purchase requisition is new"
                    },
                    "isPurchaseRequisitionNotOrdered": {
                        "type": "boolean",
                        "description": "Indicates whether the purchase requisition has not been ordered"
                    },
                    "isPurchaseRequisitionSupplied": {
                        "type": "boolean",
                        "description": "Indicates whether the purchase requisition has been supplied to vessel"
                    },
                    "isPurchaseOrderReady": {
                        "type": "boolean",
                        "description": "Indicates whether the purchase order is ready to be shipped"
                    },
                    "purchaseRequisitionDate_range": {
                        "type": "object",
                        "description": "Filter by purchase requisition date",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Start date (YYYY-MM-DD)"
                            },
                            "end_date": {
                                "type": "string",
                                "format": "date",
                                "description": "End date (YYYY-MM-DD)"
                            }
                        }
                    },
                    "purchaseOrderIssuedDate_range": {
                        "type": "object",
                        "description": "Filter by purchase order issued date",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Start date (YYYY-MM-DD)"
                            },
                            "end_date": {
                                "type": "string",
                                "format": "date",
                                "description": "End date (YYYY-MM-DD)"
                            }
                        }
                    },
                    "orderReadinessDate_range": {
                        "type": "object",
                        "description": "Filter by order readiness date (when POs are expected to be ready with vendor)",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Start date (YYYY-MM-DD)"
                            },
                            "end_date": {
                                "type": "string",
                                "format": "date",
                                "description": "End date (YYYY-MM-DD)"
                            }
                        }
                    },
                    "purchaseOrderAmount_range": {
                        "type": "object",
                        "description": "Filter by purchase order amount",
                        "properties": {
                            "min_amount": {
                                "type": "number",
                                "description": "Minimum purchase order amount"
                            },
                            "max_amount": {
                                "type": "number",
                                "description": "Maximum purchase order amount"
                            }
                        }
                    },
                    "invoiceAmount_range": {
                        "type": "object",
                        "description": "Filter by invoice amount",
                        "properties": {
                            "min_amount": {
                                "type": "number",
                                "description": "Minimum invoice amount"
                            },
                            "max_amount": {
                                "type": "number",
                                "description": "Maximum invoice amount"
                            }
                        }
                    }                
                }
            },
            "sort_by": {
                "type": "string",
                "description": "Field to sort results by. 'relevance' sorts by internal match quality (applies to keyword searches only). Other fields must be sortable in the underlying index.",
                "enum": ["relevance", "purchaseRequisitionDate", "purchaseOrderIssuedDate", "orderReadinessDate", "purchaseOrderAmount", "invoiceAmount", "weight"],
                "default": "relevance"
            },
            "sort_order": {
                "type": "string",
                "description": "Sorting order of the results",
                "enum": ["asc", "desc"],
                "default": "desc"
            },
            "max_results": {
                "type": "number",
                "description": "Maximum number of results to return",
                "default": 10,
                "minimum": 1,
                "maximum": 100
            }
        },
        "required": ["query"],
        "additionalProperties": False
        }
    ),
    types.Tool(
        name="smart_budget_search",
        description=(
            "Universal search tool for vessel budget and expense data. "
            "Primary tool for querying budget allocations, expense tracking, and financial analysis across the fleet. "
            "Handles everything from specific budget category lookups to expense variance analysis and budget performance monitoring."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Natural language or keyword query. This is matched against the fields vesselName and category. Use '*' to match all records."
                    ),
                    "default": "*"
                },
                "filters": {
                    "type": "object",
                    "description": "Optional filters to narrow the search results. Only use this if exact field values are known.",
                    "properties": {
                        "imo": {
                            "type": "number",
                            "description": "IMO number of the vessel"
                        },
                        "vesselName": {
                            "type": "string",
                            "description": "Exact or partial name of the vessel"
                        },
                        "category": {
                            "type": "string",
                            "description": "Budget category of the vessel",
                            "enum": ["CREW WAGES", "CREW EXPENSES", "VICTUALLING EXPENSES", "STORES", "SPARES", "LUBE OIL CONSUMPTION", "REPAIRS & MAINTENANCE", "MANAGEMENT FEES", "MISCELLANEOUS", "ADMINISTRATIVE EXPENSES", "INSURANCE", "DRYDOCKING EXPENSES", "NON-BUDGETED EXPENSES", "P&I/H&M EXPENSES", "VOYAGE/CHARTERERS EXPENSES", "CAPITAL EXPENDITURE", "EXTRA ORDINARY ITEMS", "VESSEL UPGRADING COSTS", "LAY-UP COSTS", "PRE-DELIVERY EXPENSES"]
                        },
                        "group": {
                            "type": "string",
                            "description": "Budget group classification. OPEX=Operating Expenses, NB=Non-Budgeted, PD=Pre-Delivery, DD=Dry-Docking",
                            "enum": ["OPEX", "NB", "PD", "DD"]
                        },
                        "period": {
                            "type": "string",
                            "description": "Budget period classification",
                            "enum": ["Previous", "Current"]
                        },
                        "budgetAmount_range": {
                            "type": "object",
                            "description": "Filter by budget amount range",
                            "properties": {
                                "min_amount": {
                                    "type": "number",
                                    "description": "Minimum budget amount"
                                },
                                "max_amount": {
                                    "type": "number",
                                    "description": "Maximum budget amount"
                                }
                            }
                        },
                        "expenseAmount_range": {
                            "type": "object",
                            "description": "Filter by expense amount range",
                            "properties": {
                                "min_amount": {
                                    "type": "number",
                                    "description": "Minimum expense amount"
                                },
                                "max_amount": {
                                    "type": "number",
                                    "description": "Maximum expense amount"
                                }
                            }
                        },
                        "date_range": {
                            "type": "object",
                            "description": "Filter by date range of the budget/expense record",
                            "properties": {
                                "start_date": {
                                    "type": "string",
                                    "format": "date",
                                    "description": "Start date (YYYY-MM-DD)"
                                },
                                "end_date": {
                                    "type": "string",
                                    "format": "date",
                                    "description": "End date (YYYY-MM-DD)"
                                }
                            }
                        }
                    }
                },
                "sort_by": {
                    "type": "string",
                    "description": "Field to sort results by. 'relevance' sorts by internal match quality (applies to keyword searches only). Other fields must be sortable in the underlying index.",
                    "enum": ["relevance", "imo", "budgetAmount", "expenseAmount", "date"],
                    "default": "relevance"
                },
                "sort_order": {
                    "type": "string",
                    "description": "Sorting order of the results",
                    "enum": ["asc", "desc"],
                    "default": "desc"
                },
                "max_results": {
                    "type": "number",
                    "description": "Maximum number of results to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["query"],
            "additionalProperties": False
        }),
    types.Tool(
        name="smart_expense_search",
        description=(
            "Universal search tool for vessel expense and cost tracking data. "
            "Primary tool for querying actual expenses, committed costs, and financial analysis across the fleet. "
            "Handles everything from specific expense lookups to cost variance analysis and budget performance monitoring."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Natural language or keyword query. This is matched against the fields vesselName and accountDescription. "
                        "Use '*' to match all records."
                    ),
                    "default": "*"
                },
                "filters": {
                    "type": "object",
                    "description": "Optional filters to narrow the search results. Only use this if exact field values are known.",
                    "properties": {
                        "imo": {
                            "type": "number",
                            "description": "IMO number of the vessel"
                        },
                        "vesselName": {
                            "type": "string",
                            "description": "Exact or partial name of the vessel"
                        },
                        "group": {
                            "type": "string",
                            "description": "Broad expense classification (use only when user explicitly specifies)",
                            "enum": ["OPEX", "NON BUDGET", "DRY DOCKING", "PRE DELIVERY"]
                        },
                        "category": {
                            "type": "string",
                            "description": "Expense sub-category within the chosen group",
                            "enum": ["ADMINISTRATIVE EXPENSES", "CAPITAL EXPENDITURE", "CREW EXPENSES", "CREW WAGES", "DRYDOCKING EXPENSES", "EXTRA ORDINARY ITEMS", "INSURANCE", "LAY-UP COSTS", "LUBE OIL CONSUMPTION", "MANAGEMENT FEES", "MISCELLANEOUS", "NON-BUDGETED EXPENSES", "PI/HM EXPENSES", "PRE-DELIVERY EXPENSES", "REPAIRS MAINTENANCE", "SPARES", "STORES", "VESSEL UPGRADING COSTS", "VICTUALLING EXPENSES", "VOYAGE/CHARTERERS EXPENSES"]
                        },
                        "expenseCategory": {
                            "type": "string",
                            "description": "Classification indicating whether the record is an actual expense or a committed cost. Unless the user specifically asks for committed cost, assume 'ACTUAL EXPENSES'",
                            "enum": ["ACTUAL EXPENSES", "COMMITTED COST"]
                        },
                        "accountNo": {
                            "type": "string",
                            "description": "Unique account number where the expense is recorded"
                        },
                        "accountDescription": {
                            "type": "string",
                            "description": "Detailed description of the expense within its category"
                        },
                        "expenseAmount_range": {
                            "type": "object",
                            "description": "Filter by actual expense amount range",
                            "properties": {
                                "min_amount": {
                                    "type": "number",
                                    "description": "Minimum expense amount"
                                },
                                "max_amount": {
                                    "type": "number",
                                    "description": "Maximum expense amount"
                                }
                            }
                        },
                        "poAmount_range": {
                            "type": "object",
                            "description": "Filter by committed PO amount range",
                            "properties": {
                                "min_amount": {
                                    "type": "number",
                                    "description": "Minimum PO amount"
                                },
                                "max_amount": {
                                    "type": "number",
                                    "description": "Maximum PO amount"
                                }
                            }
                        },
                        "expenseDate_range": {
                            "type": "object",
                            "description": "Filter by expense date range",
                            "properties": {
                                "start_date": {
                                    "type": "string",
                                    "format": "date",
                                    "description": "Start date (YYYY-MM-DD)"
                                },
                                "end_date": {
                                    "type": "string",
                                    "format": "date",
                                    "description": "End date (YYYY-MM-DD)"
                                }
                            }
                        }
                    }
                },
                "sort_by": {
                    "type": "string",
                    "description": "Field to sort results by. 'relevance' sorts by internal match quality (applies to keyword searches only). Other fields must be sortable in the underlying index.",
                    "enum": ["relevance", "imo", "expenseDate", "expenseAmount", "poAmount"],
                    "default": "relevance"
                },
                "sort_order": {
                    "type": "string",
                    "description": "Sorting order of the results",
                    "enum": ["asc", "desc"],
                    "default": "desc"
                },
                "max_results": {
                    "type": "number",
                    "description": "Maximum number of results to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["query"],
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="get_monthly_opex_budget_variance",
        description="Use this tool to get the Monthly OPEX Budget Variance Analysis for a vessel's operating expenses against the budget, highlighting categories with overspending and the top five cost contributors in each. It offers a clear snapshot of where and why variances occur, helping managers control costs effectively",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number of the vessel."
                },
                "session_id": {
                    "type": "string",
                    "description": "Optional session ID for tracking client sessions."
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="get_current_year_commited_cost",
        description="Use this tool to get details of committed costs, showing their overall value and percentage against the year-to-date OPEX budget. This also gives a breakdown of committed costs carried over from last month and those newly booked in the current month",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="get_budget_status_summary_ytd",
        description="Use this tool ,for present year till date ,to summarize OPEX variance in dollar and percentage terms, note daily OPEX against the budget, and review fund status for the year, including deficits. It highlights key overspending areas, non-budgeted expenses, and committed costs, including carryovers.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),
    # types.Tool(
    #     name="get_vessel_eta_from_email",
    #     description="Use this tool to extract a vessel's most recently reported estimated time of arrival (ETA) from emails that the vessel sends to the office (e.g., noon reports, daily position reports, arrival notices). How to use it: 1. Supply the vessel's IMO number (mandatory) - this uniquely identifies the ship. 2. The tool searches the database for processed ETA information extracted from the vessel's emails. The response includes the latest ETA information that has been extracted from the vessel's communications.",
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "imo": {
    #                 "type": "string",
    #                 "description": "The IMO number of the vessel."
    #             }
    #         },
    #         "required": ["imo"]
    #     }
    # ),
    types.Tool(
        name="get_purchase_orders_with_forwarders",
        description="Use this tool to get list of purchase orders (POs)/Spares/Items available with forwarders and ready for connection onboard the vessel",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="purchase_orders_open_more_than_180_days",
        description="Retrieves purchase orders that have been open for more than 180 days for a specific vessel.",
        inputSchema={
            "type": "object",
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number of the vessel."
                }
            },
            "required": ["imo"]
        }
    ),
    types.Tool(
        name="get_user_associated_vessels",
        description="Retrieves a list of vessels associated with a specific user.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The ID of the user to find associated vessels for."
                }
            },
            "required": ["user_id"]
        }
    ),
    # types.Tool( 
    #     name="create_update_casefile",
    #     description="Creates a structured mongoDB entry associated with a specific vessel identified by its IMO number and casefile.",
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "imo": {
    #                 "type": "integer",
    #                 "description": "IMO number uniquely identifying the vessel. Required for correctly associating the case file with the corresponding ship in the database."
    #             },
    #             "content": {
    #                 "type": "string",
    #                 "description": "The full body or detailed narrative of the case file. This may include observations, incident logs, root cause analysis, technical notes, or investigation findings related to the vessel."
    #             },
    #             "casefile": {
    #                 "type": "string",
    #                 "description": "A short and concise summary or title for the case file, such as 'Main Engine Overheating - April 2025' or 'Hull Inspection Report'. This should briefly describe the nature or subject of the entry."
    #             }
    #         },
    #         "required": ["imo", "content", "casefile"]
    #     }
    # ),
    types.Tool(
        name="get_vessel_purchase_log_table",
        description="Use this tool to get the list of purchase requisitions table for a vessel from the purchase typesense collection .Returns purchase-requisition records that were created for a specified vessel from the purchase table in the typesense collection. Example question :  Get the PR log table for VESSEL_NAME ",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {"type": "string", "description": "IMO number of the vessel"},
                "per_page": {"type": "number", "description": "Number of requisitions to return in a typesense query (maximum limit for a query is  100)"}
            },
            "additionalProperties": False
        }
    )
]


# Typesense tool definitions for mcp_purchase

typesense_tools = [
    # types.Tool(
    #     name="purchase_budget_expense_table_search",
    #     description="[FALLBACK TOOL] Search a purchase, budget or expense collection in typesense. It is mandatory to get the schema of the collection first using **get_table_schema** tool, then use the schema to search the required collection.  Use this tool when other more specialized tools have failed to provide sufficient information or when you want to search the certificate collection for a specific keyword or when more data is needed for any trend analysis that needs to be done. This is a generic search tool with less targeted results than purpose-built tools. Example questions . Expense list for <vessel> incurred in dry dock . Give me list of requsitions raised for main engine in last 6 months ",
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "collection": {
    #                 "type": "string",
    #                 "description": "Name of the collection to search",
    #                 "enum": ["purchase","budget","expense"]
    #             },
    #             "query": {
    #                 "type": "object",
    #                 "description": "Query parameters for the search"
    #             }
    #         },
    #         "required": ["collection", "query"]
    #     }
    # ),
    # types.Tool(
    #     name="purchase_budget_expense_table_search",
    #     description="[FALLBACK TOOL] Searches purchase (requisitions, orders, suppliers, invoices), budget (allocations by category), and expense (actual costs, committed amounts) databases. Use when other purchase/budget tools do not give sufficient information or for keyword searches across multiple fields or for data retreival to carry out any trend analysis. Always get the schema first using the get_purchase_budget_expense_table_schema tool . Example: For <vessel> find all requisitions raised in last 6 months for main engine spares",
    #     inputSchema={
    #         "type": "object",
    #         "properties": {
    #             "collection": {
    #                 "type": "string",
    #                 "description": "Name of the collection to search.",
    #                 "enum": ["purchase","budget","expense"]
    #             },
    #             "query": {
    #                 "type": "object",
    #                 "description": "Query object to send to Typesense's search endpoint.",
    #                 "properties": {
    #                     "q": {
    #                         "type": "string",
    #                         "description": "Search string. Use '*' to match all records."
    #                     },
    #                     "query_by": {
    #                         "type": "string",
    #                         "description": "Comma-separated list of fields to apply the `q` search on. Example: 'field1,field2'."
    #                     },
    #                     "filter_by": {
    #                         "type": "string",
    #                         "description": "Filter expression using Typesense syntax. Use ':' for equality, '<'/'>' for ranges. Combine multiple conditions using '&&' or '||'. Example: 'imo:<imo_number> && type:<certificate_type> && daysToExpiry:<cutoff_timestamp>'"
    #                     },
    #                     "include_fields": {
    #                         "type": "string",
    #                         "description": "Comma-separated list of fields to include in the results. Example: 'field1,field2,field3'."
    #                     },
    #                     "per_page": {
    #                         "type": "integer",
    #                         "description": "Number of results to return per page, defaults to 10"
    #                     }
    #                 },
    #                 "required": ["q", "query_by"]
    #             }
    #         },
    #         "required": ["collection", "query"]
    #     }
    # ),
    
    types.Tool(
        name="list_requisitions_by_status",
        description="Returns purchase-requisition records that have a certain requisition status for the specified vessel from the purchase table in the Typesense collection.",
        inputSchema={
            "type": "object",
                "required": ["imo","purchaseRequisitionStatus"],
                "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number of the vessel."
                },
                "purchaseRequisitionStatus": {
                    "type": "string",
                    "description": "It is the status of purchase requisition (PR).",
                "enum":[ "DRAFT", "APPROVED", "SENT FOR QUOTE", "AWAITING APPROVAL", "QUOTED", "PO APPROVED", "PO GENERATED", "ORDERED", "CLOSED", "CANCELLED", "PARTIALLY RECEIVED", "UNDER AMENDMENT" ]
                },
                "per_page": {
                    "type": "number",
                    "description": "Number of requisitions to return per page (default is 250)."
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID for tracking client sessions, if available"
                }
                },
                "additionalProperties": False
            }
    
    ),
    types.Tool(
        name="get_purchase_requisition_details",
        description= "Returns purchase-requisition details that match a specific purchase requisition number from the purchase collection in Typesense.",
        inputSchema={
            "type": "object",
            "required": ["purchaseRequisitionNumber"],
            "properties": {
                "purchaseRequisitionNumber": {
                "type": "string",
                "description": "Exact purchase-requisition number to retrieve."
            },
            "per_page": {
                "type": "number",
                "description": "Number of records to return per page (default is 250)."
            },
            "session_id": {
                "type": "string",
                "description": "Session ID for tracking client sessions, if available"
            }
            },
            "additionalProperties": False
        }
    ),
    # types.Tool(
    #     name="get_purchase_emails",
    #     description="Returns vessel-related email messages that are tagged as 'purchase' and were sent within the last N hours or days for a specified vessel from the diary_mails collection in Typesense. The tag 'purchase' covers all emails related to purchase , requisitions, purchase orders , invoice , quotations and vendors",
    #     inputSchema={
    #        "type": "object",
    #        "required": ["imo", "tag"],
    #        "properties": {
    #            "imo": {
    #                "type": "string",
    #                "description": "The IMO number or name of the vessel"
    #            },
    #            "tag": {
    #                "type": "string",
    #                "description": "The tag to be searched in the emails",
    #                "enum": ["purchase"]
    #            },
    #            "lookbackHours": {
    #                "type": "integer",
    #                "description": "Rolling window size in hours (e.g., 24 = last day).Optional - Only if a specific window period is provided by the user"
    #            },
    #            "per_page": {
    #                "type": "number",
    #                "description": "Number of requisitions to return per page (default is 250)"
    #            }
    #        },
    #        "additionalProperties": False
    #    }
    # ),
    # types.Tool(
    #     name="get_purchase_casefiles",
    #     description="Use this tool to fetch all vessel-related case files that mention the word \"purchase\",\"budget\" , \"expense\" and were sent within a recent time window:\n1. Take the current date-and-time (UTC).\n2. Subtract the desired look-back period (X hours or days) and get calculated_date_time.\n3. Query the caseFiles collection for case files whose lastCasefileUpdateDate is greater than  the calculated_date_time **and** casefile field has the keyword.\nProvide the vessel's IMO (or name) and the Date and time from step 2; optionally set how many results you want per page. Example Question: Give me list of purchase related emails in last 24 hours",
    #     inputSchema={
    #         "type": "object",
    #         "required": ["imo","lookback_hours", "query_keyword"],
    #         "properties": {
    #             "imo": {
    #                 "type": "string",
    #                 "description": "IMO number of the vessel"
    #             },
    #             "lookback_hours": {
    #                 "type": "integer",
    #                 "description": "Lookback hours in the request"
    #             },
    #             "query_keyword": {
    #                 "type": "string",
    #                 "description": "The keyword to be searched in the casefiles"
    #             },
    #             "per_page": {
    #                 "type": "integer",
    #                 "description": "Number of casefiles to return per page"
    #             }
    #         },
    #         "additionalProperties": False
    #     }
    # ),
     types.Tool(
        name="list_recent_vessel_purchase_requisitions",
        description="Returns purchase-requisition records that were created within the last N hours or days for a specified vessel from the purchase table in the typesense collection.",
        inputSchema={
            "type": "object",
            "required": ["imo", "lookbackHours"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number or name of the vessel"
                },
                "lookbackHours": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 720,
                    "description": "Rolling window size in hours (e.g., 24 = last day)."
                },
                "per_page": {
                    "type": "number",
                    "description": "Number of requisitions to return per page (default is 250)"
                }
            },
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="get_vessel_details",
        description="Retrieves vessel details including IMO number, vessel name,class,flag,DOC and the ERP version for a specific vessel.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string", 
                    "description": "Pass the vessel name to search for the IMO number"
                }
            },
            "required": ["query"]
        }
    ),

    types.Tool(
        name="list_overdue_open_requisitions",
        description="Retrieves purchase-requisition records that remain in OPEN stage and were raised more than X days ago for a specified vessel from the purchase table in the Typesense collection.",
        inputSchema={
            "type": "object",
            "required": ["imo", "daysOverdue", "stage"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number or name of the vessel."
                },
                "daysOverdue": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 1000,
                    "description": "Number of days before today to use as cutoff date."
                },
                "stage": {
                    "type": "string",
                    "description": "Stage to filter by (OPEN or CLOSE).",
                    "enum": ["OPEN", "CLOSE"]
                },
                "per_page": {
                    "type": "number",
                    "description": "Number of requisitions to return per page (default is 250)."
                }
            },
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="list_purchase_orders_by_status",
        description="Returns purchase-order records that match a status for a specified vessel from the purchase table in the Typesense collection.",
        inputSchema={
            "type": "object",
            "required": ["imo", "purchaseOrderStatus"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number of the vessel."
                },
                "purchaseOrderStatus": {
                    "type": "string",
                    "description": "Status of the purchase order.",
                    "enum": ["CLOSED", "WITH FORWARDER", "CANCELLED", "ORDERED", "AWAITING APPROVAL", "UNDER AMENDMENT", "APPROVED", "DRAFT", "REJECTED", "QUOTED"]
                },
                "per_page": {
                    "type": "number",
                    "description": "Number of purchase orders to return per page (default is 250)."
                }
            },
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="list_requisitions_by_type_and_stage",
        description="Returns purchase-requisition records for a specified vessel, filtered by requisition type (e.g., MAINTENANCE CHEMICALS, SPARE PARTS, etc.) and purchase-order stage (OPEN or CLOSE). Results are sorted by requisition date in descending order so the first item represents the most recent supply event.",
        inputSchema={
            "type": "object",
            "required": ["imo", "purchaseRequisitionType", "purchaseOrderStage"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                },
                "purchaseRequisitionType": {
                    "type": "string",
                    "enum": [
                        "ANTI-PIRACY ITEMS",
                        "CHARTS PUBLICATIONS",
                        "FLAG LOG BOOKS",
                        "FUEL ADDITIVES",
                        "GAS MEASUREMENT EQUIPMENTS",
                        "GASES WELDING",
                        "GENERAL STORES",
                        "LICENSE",
                        "LSA-FFA",
                        "LUBE OILS GREASES",
                        "MAINTENANCE CHEMICALS",
                        "PAINTS THINNERS",
                        "SYNERGY PPE KIT",
                        "PERSONNEL PROTECTION",
                        "SAFETY",
                        "SCRUBBER BWTS CHEMICALS",
                        "MARPOL SEALS",
                        "SERVICE",
                        "SPARE PARTS",
                        "PRINTED STATIONARY KITS",
                        "STORE",
                        "TANK/HOLD CLEANING CHEMICALS"
                    ],
                    "description": "Category of the requisition to filter."
                },
                "purchaseOrderStage": {
                    "type": "string",
                    "enum": ["OPEN", "CLOSE"],
                    "description": "Stage of the purchase order (use CLOSE to find the most recently supplied items)."
                },
                "vesselName": {
                    "type": "string",
                    "description": "Optional vessel name (additional filter when needed)."
                },
                "per_page": {
                    "type": "number",
                    "description": "Number of records to return per page (default 250)."
                }
            },
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="list_recent_requisitions_by_order_priority",
        description="Returns purchase-requisition records flagged with a certain priority that were created within the last X days for a specified vessel from the purchase table in the Typesense collection.",
        inputSchema={
            "type": "object",
            "required": [
                "imo",
                "daysAgo"
            ],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "The IMO number or name of the vessel."
                },
                "daysAgo": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 1000,
                    "description": "Number of days to look back for requisitions."
                },
                "per_page": {
                    "type": "number",
                    "description": "Number of requisitions to return per page (default is 250)."
                },
                "orderPriority": {
                    "type": "string",
                    "description": "It is about the priority of the purchase requisition or order",
                    "enum": ["DEFECT", "ROUTINE MAINTENANCE STOCK", "NORMAL", "RECOMMENDED STOCK", "URGENT", "OTHERS", "DRY DOCK", "AUDIT"]
                }
            },
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="get_purchase_order_details",
        description="Returns purchase-order details that match a specific purchase order number from the purchase collection in Typesense.",
        inputSchema={ "type": "object",
            "required": ["purchaseOrderNumber"],
            "properties": {
                "purchaseOrderNumber": {
                    "type": "string",
                    "description": "It is the purchase order number to be searched for"
                },
                "per_page": {
                    "type": "number",
                    "description": "Number of purchase orders to return in a typesense query (maximum limit for a query is  250)"
                }
             },
            "additionalProperties": False
        }
    ),
     types.Tool(
        name = "find_relevant_vendors",
        description = "Searches for vendors by matching on service, location, and/or name. Supports synonym expansion and relevance-based ranking to find the most suitable vendors.",
        inputSchema = {
            "type": "object",
            "properties": {
                "vendorName": {
                    "type": "string",
                    "description": "Name of the vendor the user is looking for if any"
                },
                "service": {
                    "type": "string",
                    "description": "Service the vendor provides the user is looking for if any"
                },
                "locationRegion": {
                    "type": "string",
                    "description": "Location of the vendor the user is looking for if any"
                }
            },
            "required": []
        }
    ),
    types.Tool(
        name="list_committed_cost_expenses",
        description="Retrieve expense records for a vessel that are classified as **\"COMMITTED COST\"** (i.e., the amount has been reserved on a purchase order but not yet spent).\n\nHow to use it\n1. Supply the vessel's IMO number.\n2. The tool automatically applies the filter `expenseCategory=COMMITTED COST`.\n3. Optional filters:\n   • `group` – one of OPEX, NON BUDGET, DRY DOCKING, PRE DELIVERY.\n   • `category` – any budget sub-category in the enum list below (SPARES, STORES, etc.).\n   • `dateFrom` and `dateTo` – ISO dates (`YYYY-MM-DD`) to restrict the `expenseDate` range.\n4. The query sent to the *expense* collection looks like\n   `imo=[IMO] AND expenseCategory:\"COMMITTED COST\"` plus any optional filters.\n5. Results include `group`, `category`, `accountNo`, `accountDescription`, `expenseDate`, `poAmount`, and other PO metadata.",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                },
                "group": {
                    "type": "string",
                    "enum": ["OPEX", "NON BUDGET", "DRY DOCKING", "PRE DELIVERY"],
                    "description": "Optional broad expense group (use only if the user specifies it)."
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "ADMINISTRATIVE EXPENSES",
                        "CAPITAL EXPENDITURE",
                        "CREW EXPENSES",
                        "CREW WAGES",
                        "DRYDOCKING EXPENSES",
                        "EXTRA ORDINARY ITEMS",
                        "INSURANCE",
                        "LAY-UP COSTS",
                        "LUBE OIL CONSUMPTION",
                        "MANAGEMENT FEES",
                        "MISCELLANEOUS",
                        "NON-BUDGETED EXPENSES",
                        "PI/HM EXPENSES",
                        "PRE-DELIVERY EXPENSES",
                        "REPAIRS MAINTENANCE",
                        "SPARES",
                        "STORES",
                        "VESSEL UPGRADING COSTS",
                        "VICTUALLING EXPENSES",
                        "VOYAGE/CHARTERERS EXPENSES"
                    ],
                    "description": "Optional sub-category filter; omit to include all categories."
                },
                "dateFrom": {
                    "type": "string",
                    "description": "Optional earliest expenseDate (inclusive) in YYYY-MM-DD format."
                },
                "dateTo": {
                    "type": "string",
                    "description": "Optional latest expenseDate (inclusive) in YYYY-MM-DD format."
                },
                "per_page": {
                    "type": "number",
                    "description": "Number of records per page (default 50)."
                }
            },
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="list_recent_urgent_requisitions",
        description="Returns purchase-requisition records whose `orderPriority` is **\"URGENT\"** and whose `purchaseRequisitionDate` falls within the last *N* days for a specified vessel.",
        inputSchema={
            "type": "object",
            "required": ["imo", "daysAgo"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                },
                "daysAgo": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 1000,
                    "description": "How many days back to look for urgent requisitions."
                },
                "per_page": {
                    "type": "number",
                    "description": "Number of requisitions to return per page (default 50)."
                }
            },
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="get_vessel_budget_data",
        description="Returns budget figures for a specified vessel from the budget table collection in Typesense, with optional filters for budget category, group, period, and a custom date range.",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "CREW WAGES", "CREW EXPENSES", "VICTUALLING EXPENSES", "STORES", "SPARES", "LUBE OIL CONSUMPTION", "REPAIRS & MAINTENANCE", "MANAGEMENT FEES", "MISCELLANEOUS", "ADMINISTRATIVE EXPENSES", "INSURANCE", "DRYDOCKING EXPENSES", "NON-BUDGETED EXPENSES", "P&I/H&M EXPENSES", "VOYAGE/CHARTERERS EXPENSES", "CAPITAL EXPENDITURE", "EXTRA ORDINARY ITEMS", "VESSEL UPGRADING COSTS", "LAY-UP COSTS", "PRE-DELIVERY EXPENSES"
                    ],
                    "description": "Budget category to filter (omit to return all categories)."
                },
                "group": {
                    "type": "string",
                    "enum": ["OPEX", "NB", "PD", "DD"],
                    "description": "Category group to filter (OPEX, NB, PD, DD)."
                },
                "period": {
                    "type": "string",
                    "enum": ["PREVIOUS YEAR", "CURRENT YEAR"],
                    "description": "Reporting period to filter (omit for all periods)."
                },
                "dateFrom": {
                    "type": "number",
                    "description": "UNIX-epoch timestamp (seconds) for the start of the date range, inclusive."
                },
                "dateTo": {
                    "type": "number",
                    "description": "UNIX-epoch timestamp (seconds) for the end of the date range, inclusive."
                },
                "per_page": {
                    "type": "number",
                    "description": "Number of records to return per page (default is 250)."
                }
            },
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="get_all_vessel_purchase_requisitions",
        description="Use this tool to export ALL purchase requisitions for a vessel from the purchase typesense collection using the export method. Unlike this tool get_vessel_purchase_log_table which is limited to 100 records, this tool retrieves the complete dataset of purchase requisitions for comprehensive analysis, reporting, or bulk data processing. Optionally filter by date range using purchaseRequisitionDate field for specific time periods. Use this when you need: complete purchase history analysis, bulk data export for reporting, comprehensive spend analysis, or when the user specifically asks for 'all' or 'complete' purchase data. Use the table tool instead when you need quick overview, recent transactions, or paginated display. Example questions: 'Export all purchase requisitions for VESSEL_NAME', 'Get complete purchase history for last 6 months for VESSEL_NAME', 'Download all PR data for VESSEL_NAME since MM YYYY",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {"type": "string", "description": "IMO number of the vessel"},
                "start_date": {"type": "string", "description": "Optional start date for filtering requisitions (YYYY-MM-DD format). Filter will include requisitions from this date onwards based on purchaseRequisitionDate field"},
                "end_date": {"type": "string", "description": "Optional end date for filtering requisitions (YYYY-MM-DD format). Filter will include requisitions up to this date based on purchaseRequisitionDate field"}
            },
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="get_vessel_expense_data",
        description="Use this tool to export ALL expense records for a vessel from the expense typesense collection using the export method. This tool retrieves the complete dataset of expense records for comprehensive financial analysis, audit reporting, or bulk data processing. Optionally filter by date range using expenseDate field for specific time periods. Use this when you need: complete expense history analysis, financial audit data export, comprehensive cost analysis across time periods, or when the user specifically asks for 'all' or 'complete' expense data. Use other expense tools instead when you need quick lookups, filtered searches, or specific expense categories. Example questions: 'Export all expenses for VESSEL_NAME', 'Get complete expense history for last year for VESSEL_NAME', 'Download all expense data for VESSEL_NAME since March 2024'",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {"type": "string", "description": "IMO number of the vessel"},
                "start_date": {"type": "string", "description": "Optional start date for filtering expense records (YYYY-MM-DD format). Filter will include expenses from this date onwards based on expenseDate field"},
                "end_date": {"type": "string", "description": "Optional end date for filtering expense records (YYYY-MM-DD format). Filter will include expenses up to this date based on expenseDate field"}
            },
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="get_complete_vessel_budget_data",
        description="Use this tool to export ALL budget records for a vessel from the budget typesense collection using the export method. This tool retrieves the complete dataset of budget records for comprehensive financial planning, budget variance analysis, or bulk data processing. Optionally filter by date range using date field for specific time periods. Use this when you need: complete budget history analysis, multi-year budget comparisons, comprehensive budget vs actual analysis, or when the user specifically asks for 'all' or 'complete' budget data. Use other budget tools instead when you need quick budget lookups, specific categories, or current period data. Example questions: 'Export all budget data for VESSEL_NAME', 'Get complete budget history for last 2 years for VESSEL_NAME', 'Download all budget records for VESSEL_NAME since 2023'",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {"type": "string", "description": "IMO number of the vessel"},
                "start_date": {"type": "string", "description": "Optional start date for filtering budget records (YYYY-MM-DD format). Filter will include budget records from this date onwards based on date field"},
                "end_date": {"type": "string", "description": "Optional end date for filtering budget records (YYYY-MM-DD format). Filter will include budget records up to this date based on date field"}
            },
            "additionalProperties": False
        }
    ),
]





# Communication Tools

# communication_tools = [
#     types.Tool(
#         name="mail_communication",
#         description=(
#             "Use this tool to send formal emails to one or more recipients. "
#             "It supports a subject line, an HTML-formatted email body, and optional CC and BCC fields. "
#             "Use this tool when you have email addresses of the people you want to contact. You can send the same message to many people at once.."
#         ),
#         inputSchema={
#             "type": "object",
#             "properties": {
#                 "subject": {
#                     "type": "string",
#                     "description": (
#                         "The subject line of the email. Keep it concise and professional. "
#                         "Maximum length is 100 characters."
#                     ),
#                     "maxLength": 100
#                 },
#                 "content": {
#                     "type": "string",
#                     "description": (
#                         "The main content of the email, written in HTML. "
#                         "This allows formatting like bold text, lists, and links. "
#                         "End the message with the signature: 'Best regards,<br>Syia'."
#                     )
#                 },
#                 "recipient": {
#                     "type": "array",
#                     "description": (
#                         "A list of email addresses for the main recipients (To field). "
#                         "Must contain at least one valid email address."
#                     ),
#                     "items": {"type": "string", "format": "email"},
#                     "examples": [["example@domain.com"]]
#                 },
#                 "cc": {
#                     "type": "array",
#                     "description": (
#                         "Optional list of email addresses to be included in the CC (carbon copy) field."
#                     ),
#                     "items": {"type": "string", "format": "email"}
#                 },
#                 "bcc": {
#                     "type": "array",
#                     "description": (
#                         "Optional list of email addresses to be included in the BCC (blind carbon copy) field."
#                     ),
#                     "items": {"type": "string", "format": "email"}
#                 }
#             },
#             "required": ["subject", "content", "recipient"]
#         }
#     ),
#     types.Tool(
#         name="whatsapp_communication",
#         description=(
#             "Use this tool to send quick, informal text messages via WhatsApp. "
#             "It is designed for real-time, individual communication using a phone number. "
#             "Only one phone number can be messaged per tool call."
#         ),
#         inputSchema={
#             "type": "object",
#             "properties": {
#                 "content": {
#                     "type": "string",
#                     "description": (
#                         "The message to send. Must be plain text. "
#                         "Keep the message short and to the point."
#                     )
#                 },
#                 "recipient": {
#                     "type": "string",
#                     "description": (
#                         "The recipient's WhatsApp phone number. "
#                         "It can be in international E.164 format (e.g., +14155552671) or a local number (e.g., 9876543210), "
#                         "which will be automatically normalized."
#                     ),
#                     "pattern": "^(\+?[1-9]\\d{1,14}|\\d{6,15})$",
#                     "examples": ["+919876543210", "9876543210"]
#                 }
#             },
#             "required": ["content", "recipient"]
#         }
#     )
# ]


# Document Parser Tools
document_parser_tools = [
    types.Tool(
        name="parse_document_link",
        description="Use this tool to parse a document from a link or from local file. The tool will parse the document and return the text content.",
        inputSchema={
            "type": "object",
            "required": ["document_link"],
            "properties": {
                "document_link": {
                    "type": "string",
                    "description": "The link to the document that needs to be parsed"
                }
            },
            "additionalProperties": False
        }
    )
]

# Document Parser Tools
general_tools = [
    types.Tool(
        name="google_search",
        description="Perform a Google search using a natural language query. Returns relevant web results.",
        inputSchema={
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to be executed."
                }
            },
            "additionalProperties": False
        }
    )
]

# Vendor Tools
vendor_tools = [
    types.Tool(
        name = "get_vendor_contact_details",
        description = "Returns contact information (address, phone number, email) for a specific vendor by name. Use this tool when the user is asking for a vendor's contact information or how to reach a vendor.",
        inputSchema = {
            "type": "object",
            "properties": {
                "vendorName": {
                    "type": "string",
                    "description": "Name of the vendor the user is looking for"
                }
            },
            "required": ["vendorName"]
        }
    ),
    types.Tool(
        name="list_top_expenses_by_category",
        description="Return a vessel's **highest-value expense records** (expenseCategory = \"ACTUAL EXPENSES\") so the user can pick the top *N* items in **each budget category**.\n\nHow it works\n1. Always filter on `imo = <IMO>` and `expenseCategory = \"ACTUAL EXPENSES\"`.\n2. Sort the result set by `expenseAmount:desc` so the costliest items appear first.\n3. The tool can optionally narrow the search by a `group` (OPEX, NON BUDGET, DRY DOCKING, PRE DELIVERY) or by an ISO `dateFrom/dateTo` window on `expenseDate`.\n4. The caller sets `topN` (default **5**).  Because Typesense does not group-limit natively, the LLM should:\n   • Call this tool with a sufficiently large `per_page` (e.g. 100).\n   • Post-process the returned list, taking the first *N* rows **per unique category**.\n\nExample use-case: \"Give me the top 5 expenses for each category for VESSEL_NAME.\" → call with `{ imo:\"IMO_NUMBER\", topN:5 }`, then slice the response per category on the LLM side.",
        inputSchema={
            "type": "object",
            "required": ["imo"],
            "properties": {
                "imo": {
                    "type": "string",
                    "description": "IMO number of the vessel."
                },
                "topN": {
                    "type": "number",
                    "description": "How many of the largest expenses to return per category (default 5)."
                },
                "group": {
                    "type": "string",
                    "enum": ["OPEX", "NON BUDGET", "DRY DOCKING", "PRE DELIVERY"],
                    "description": "Optional high-level group filter (use only if the user asks for it)."
                },
                "dateFrom": {
                    "type": "string",
                    "description": "Optional earliest expenseDate (inclusive) in YYYY-MM-DD format."
                },
                "dateTo": {
                    "type": "string",
                    "description": "Optional latest expenseDate (inclusive) in YYYY-MM-DD format."
                },
                "per_page": {
                    "type": "number",
                    "description": "Number of records to fetch (default 100).  Use a value large enough to cover topN items for every category."
                }
            },
            "additionalProperties": False
        }
    )]


casefile_tools = [
# Tool 1: Write Casefile Data
    types.Tool(
        name="write_casefile_data",
        description=(
            "Creates or updates casefile-related data. "
            "Supports two distinct operations:\n"
            "- write_casefile: Create or update casefile metadata (e.g., summary, title, importance).\n"
            "- write_page: Add or update a page under an existing casefile, including content and indexing."
            "Only pass arguments explicitly required or allowed for the chosen operation."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["write_casefile", "write_page"],
                    "description": (
                        "Specifies the writing operation: 'write_casefile' for creating new casefile or 'write_page' for page content of already existing casefile."
                    )
                },
                "casefile_url":{
                    "type": "string",
                    "description": (
                        "The unique identifier of the casefile,  direct casefile url link."
                        "Required for 'write_page'."
                    )
                },
                 "casefileName": {
                    "type": "string",
                    "enum": ["Purchase"],
                    "description": (
                        "Required for 'write_casefile'. Name of the casefile"
                    )
                },
                "category": {
                    "type": "string",
                    "enum": ["purchase"],
                    "description": (
                        "Required for 'write_casefile' . Category of the casefile"
                    )
                },
                "currentStatus": {
                    "type": "string",
                    "description": (
                        "<review the casefile and plan to create current status in one line, highlighting keywords>"
                        "Required for 'write_casefile': Current status of the casefile, it will be of 4-5 words."
                        "Required for 'write_page': update or kept it same status of the casefile based on recent received email. it willbe of 4-5 words."
                    )
                },
                "casefileSummary": {
                    "type": "string",
                    "description": (
                        "Required for 'write_casefile'. Summary or high-level description of the casefile.\n"
                        "Optional for 'write_page': can provide updated summary if needed."
                    )
                },
                "importance": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": (
                        "It will show the importance of the casefile reference for the urgency and importance of the matter in the casefile."
                        "Required for 'write_casefile'. Importance score of the casefile (0–100).\n"
                        "required for 'write_page': can provide an updated score based on the new email content added to the casefile."
                    )
                },
                "imo": {
                    "type": "number",
                    "description": (
                        "Required for 'write_casefile'. IMO number of the associated vessel."
                    )
                },
                "role": {
                    "type": "string",
                    "enum": ["incident", "legal", "regulatory", "other"],
                    "description": (
                        "Required for 'write_casefile'. Role/category of the casefile."
                    )
                },
                "summary": {
                    "type": "string",
                    "description": (
                        "Required for 'write_page'. Detailed content or summary of the new page."
                    )
                },
                "topic": {
                    "type": "string",
                    "description": (
                        "Required for 'write_page'.It is of 4-8 words aboyt what this document is about."
                    )
                },
                "facts": {
                    "type": "string",
                    "description": (
                        "Required for 'write_page'..It will  have the highlighted facts/information from the database."
                    )
                },
                "detailed_report":{
                    "type": "string",
                    "description": (
                        "Required for 'write_page'. It will have the detailed report of the casefile in markdown format."
                    )
                },

                
                "links": {
                    "type": "array",
                    "items": {  
                        "type": "string"
                    },
                    "description": (
                        "Required for 'write_page'. Relevent links you want to add to the case file."
                    )
                }
            },
            "required": ["operation"],
            "additionalProperties": False
        }
    ),
    types.Tool(
        name="retrieve_casefile_data",
        description=(
            "Retrieves data from casefiles. "
            "Supports the following operations:\n"
            "- get_casefiles: List all casefiles for a vessel matching a text query.\n"
            "- get_casefile_plan: Retrieve the latest plan associated with a specific casefile.\n"
            "Only pass arguments explicitly required or allowed for the chosen operation."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["get_casefiles","get_casefile_plan"],
                    "description": "Specifies the retrieval operation."
                },
                "imo": {
                    "type": "number",
                    "description": (
                        "Required for 'get_casefiles'. IMO number of the vessel."
                    )
                },
                "casefile_url": {
                "type": "string",
                "description": "The unique identifier of the casefile,  direct casefile url link. Required for operation get_casefile_plan."
                },
                "query": {
                    "type": "string",
                    "description": (
                        "Optional for 'get_casefiles'. search query to filter casefiles based on the context and user query."
                    )
                },
                "min_importance": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100,
                    "description": (
                        "Optional for 'get_casefiles'. Filter results with importance score ≥ this value."
                    )
                },
                "pagination": {
                    "type": "number",
                    "default": 1,
                    "description": (
                        "optional for 'get_casefiles'. Page number for paginated results."

                    )
                },
                "page_size": {
                    "type": "number",
                    "default": 10,
                    "description": (
                        "Optional for 'get_casefiles'. Number of results per page."
                    )
                }
            },
            "required": ["operation"]
        }
    )


]


# Combined tools for compatibility
tool_definitions = typesense_tools + mongodb_tools +  document_parser_tools + general_tools + vendor_tools + casefile_tools


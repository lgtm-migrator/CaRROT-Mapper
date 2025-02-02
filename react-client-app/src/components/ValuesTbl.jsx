import React, { useState, useEffect, useRef } from 'react'
import {
    Button,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    TableCaption,
    Text,
    HStack,
    VStack,
    Flex,
    Spinner,
    ScaleFade,
    Input,
    useDisclosure,
    Link
} from "@chakra-ui/react"

import { Formik, Form } from 'formik'
import { getScanReports, getScanReportField, getScanReportTable, useGet } from '../api/values'
import ConceptTag from './ConceptTag'
import ToastAlert from './ToastAlert'
import PageHeading from './PageHeading'
import CCBreadcrumbBar from './CCBreadcrumbBar'
import Error404 from '../views/Error404'

const ValuesTbl = (props) => {
    // get value to use in query from page url
    const pathArray = window.location.pathname.split("/")
    const scanReportFieldId = pathArray[pathArray.length - 2]
    const scanReportId = pathArray[pathArray.length - 6]
    // set page state variables
    const [alert, setAlert] = useState({ hidden: true, title: '', description: '', status: 'error' });
    const { isOpen, onOpen, onClose } = useDisclosure()
    const [scanReports, setScanReports] = useState([]);
    const [error, setError] = useState(undefined);
    const [loadingMessage, setLoadingMessage] = useState("");
    const scanReportsRef = useRef([]);
    const scanReportTable = useRef([]);
    const scanReportField = useRef([]);
    const [mappingButtonDisabled, setMappingButtonDisabled] = useState(true);
    const scanReportName = useRef([]);

    useEffect(() => {
        props.setTitle(null)
        // Check user can see SR field
        useGet(`/scanreportfields/${scanReportFieldId}`).then(
            res => {
                // get and store scan report table object to use to check person_id and date_event
                getScanReportField(scanReportFieldId).then(data => {
                    scanReportField.current = data
                    getScanReportTable(data.scan_report_table).then(table => {
                        scanReportTable.current = table
                        setMappingButtonDisabled(false)
                    })
                })
                // get scan report values
                getScanReports(scanReportFieldId, setScanReports, scanReportsRef, setLoadingMessage, setError)
                useGet(`/scanreports/${scanReportId}/`).then(sr => scanReportName.current = sr.dataset)
            }
        ).catch(
            err => {
                // If user can't see SR field, show an error message
                setError(true)
                setLoading(false)
            }
        )
    }, []);

    // called to submit a concept to be added. Calls handle submit function from app.js
    const handleSubmit = (id, concept) => {
        props.handleSubmit(id, concept, scanReportsRef, setScanReports, setAlert, onOpen, scanReportTable.current, 17)
    }

    // called to delete a concept. Calls handle delete function from app.js
    const handleDelete = (id, conceptId) => {
        props.handleDelete(id, conceptId, scanReportsRef, setScanReports, setAlert, onOpen)
    }

    if (error) {
        //Render Loading State
        return <Error404 setTitle={props.setTitle} />
    }

    if (scanReports.length < 1) {
        //Render Loading State
        return (
            <Flex padding="30px">
                <Spinner />
                <Flex marginLeft="10px">Loading Values {loadingMessage}</Flex>
            </Flex>
        )
    }
    if (scanReports[0] == undefined) {
        //Render Loading State
        return (
            <Flex padding="30px">

                <Flex marginLeft="10px">No Values Found</Flex>
            </Flex>
        )
    }
    else {
        return (
            <div>
                <CCBreadcrumbBar>
                    <Link href={"/"}>Home</Link>
                    <Link href={"/scanreports/"}>Scan Reports</Link>
                    <Link href={`/scanreports/${scanReportTable.current.scan_report}/`}>{scanReportName.current}</Link>
                    <Link href={`/scanreports/${scanReportTable.current.scan_report}/tables/${scanReportTable.current.id}/`}>{scanReportTable.current.name}</Link>
                    <Link href={`/scanreports/${scanReportTable.current.scan_report}/tables/${scanReportTable.current.id}/fields/${scanReportField.current.id}/`}>{scanReportField.current.name}</Link>
                </CCBreadcrumbBar>
                <PageHeading text={"Values"} />
                <Flex my="10px">
                    <HStack>
                        <Link href={"/scanreports/" + scanReportId + "/details/"}>
                            <Button variant="blue" my="10px">Scan Report Details</Button>
                        </Link>
                        <Link href={"/scanreports/" + scanReportId + "/mapping_rules/"}>
                            <Button isDisabled={mappingButtonDisabled} variant="blue" my="10px">Go to Rules</Button>
                        </Link>
                        {window.canEdit && <Link href={"/scanreports/" + scanReportId + "/tables/" + scanReportTable.current.id + "/update/"}>
                            <Button variant="blue" my="10px">Edit Table</Button>
                        </Link>
                        }
                    </HStack>
                </Flex>
                {isOpen &&
                    <ScaleFade initialScale={0.9} in={isOpen}>
                        <ToastAlert hide={onClose} title={alert.title} status={alert.status} description={alert.description} />
                    </ScaleFade>
                }

                <Table variant="striped" colorScheme="greyBasic">
                    <TableCaption></TableCaption>
                    <Thead>
                        <Tr>
                            <Th>Value</Th>
                            <Th>Value Description</Th>
                            <Th>Frequency</Th>
                            <Th>Concepts</Th>
                            <Th px={2}></Th>
                        </Tr>
                    </Thead>
                    <Tbody>
                        {
                            // Create new row for every value object
                            scanReports.map((item, index) =>
                                <Tr key={item.id}>
                                    <Td maxW={"300px"}>{item.value}</Td>
                                    <Td maxW={"300px"}>{item.value_description}</Td>
                                    <Td maxW={"300px"}>{item.frequency}</Td>

                                    <Td maxW={"300px"}>
                                        {item.conceptsLoaded ?
                                            item.concepts.length > 0 &&
                                            <VStack alignItems='flex-start' >
                                                {item.concepts.map((concept) => (
                                                    <ConceptTag
                                                        key={concept.concept.concept_id}
                                                        conceptName={concept.concept.concept_name}
                                                        conceptId={concept.concept.concept_id.toString()}
                                                        conceptIdentifier={concept.id.toString()}
                                                        itemId={item.id} handleDelete={handleDelete}
                                                        creation_type={concept.creation_type ? concept.creation_type : undefined}
                                                        readOnly={!window.canEdit}
                                                    />
                                                ))}
                                            </VStack>
                                            :
                                            item.conceptsLoaded === false ?
                                                <Flex >
                                                    <Spinner />
                                                    <Flex marginLeft="10px">Loading Concepts</Flex>
                                                </Flex>
                                                :
                                                <Text>Failed to load concepts</Text>
                                        }
                                    </Td>
                                    <Td w={"150px"} px={2}>

                                        <Formik initialValues={{ concept: '' }} onSubmit={(data, actions) => {
                                            handleSubmit(item.id, data.concept)
                                            actions.resetForm();
                                        }}>
                                            {({ values, handleChange, handleBlur, handleSubmit }) => (
                                                <Form onSubmit={handleSubmit}>
                                                    <HStack>
                                                        <Input
                                                            w={"105px"}
                                                            type='number'
                                                            name='concept'
                                                            value={values.concept}
                                                            onChange={handleChange}
                                                            onBlur={handleBlur}
                                                            isDisabled={!window.canEdit}
                                                        />
                                                        <div>
                                                            <Button type='submit' isDisabled={!((item.conceptsToLoad == 0) || window.canEdit)} backgroundColor='#3C579E' color='white'>Add</Button>
                                                        </div>
                                                    </HStack>
                                                </Form>
                                            )}
                                        </Formik>
                                    </Td>
                                </Tr>

                            )
                        }
                    </Tbody>
                </Table>
            </div>
        )

    }

}


export default ValuesTbl


import React, { useState, useEffect, useRef } from 'react'
import {
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    TableCaption,
    HStack,
    VStack,
    Flex,
    Spinner,
    Link,
    Select,
    Button,
    useDisclosure,
} from "@chakra-ui/react"

import { ArrowForwardIcon } from '@chakra-ui/icons'
import { useGet } from '../api/values'
import ConceptTag from './ConceptTag'
import MappingModal from './MappingModal'
import SummaryTbl from './SummaryTbl'
import RulesTbl from './RulesTbl'



const MappingTbl = () => {
    const scan_report_id = window.location.href.split("scanreports/")[1].split("/")[0]
    const [values, setValues] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(undefined);
    const [loadingMessage, setLoadingMessage] = useState("");
    const [mapDiagram, setMapDiagram] = useState({ showing: false, image: null });
    const svg = useRef(null);
    const [destinationTableFilter, setDestinationTableFilter] = useState([]);
    const [sourceTableFilter, setSourceTableFilter] = useState([]);
    const [filters, setFilters] = useState([]);
    const [isDownloading, setDownloading] = useState(false);
    const [isDownloadingCSV, setDownloadingCSV] = useState(false);
    const [isDownloadingImg, setDownloadingImg] = useState(false);
    const downLoadingImgRef = useRef(false)
    const { isOpen, onOpen, onClose } = useDisclosure()

    useEffect(() => {
        // on initial load of the page,
        // get all mapping rules for the page unfiltered
        useGet(`/mappingruleslist/?id=${scan_report_id}`).then(res => { // not sure if this needs a / on the end or not as it's an undocumented endpoint
            setValues(res[0].sort((a, b) => (a.rule_id > b.rule_id) ? 1 : ((b.rule_id > a.rule_id) ? -1 : 0)))
            setLoading(false);
            setLoadingMessage("");
        })
            .catch(err => {
                setLoading(false);
                setLoadingMessage("");
                setError("An error has occured while fetching the rules")
            })
    }, []);

    useEffect(() => {
        // run when map diagram state has changed
        if (!mapDiagram.image) {
            // if no map diagram is loaded, request to get a new one
            const result = await usePost(window.location.href, { 'get_svg': true }, false);
            const diagramString = await result.text()
            var parser = new DOMParser();
            var diagram = parser.parseFromString(diagramString, "text/html");

            setMapDiagram((mapDiagram2) => ({ ...mapDiagram2, image: diagram.getElementsByTagName("svg")[0] }));
            if (svg.current) {
                if (svg.current.hasChildNodes()) {
                    while (svg.current.firstChild) {
                        svg.current.removeChild(svg.current.lastChild);
                    }
                }
                svg.current.appendChild(diagram.getElementsByTagName("svg")[0]);
            }
            if (downLoadingImgRef.current == true) {
                downloadImage(diagram.getElementsByTagName("svg")[0]);
            }
        }
        else {
            if (svg.current) {
                if (svg.current.hasChildNodes()) {
                    // remove all other diagrams if they exist
                    while (svg.current.firstChild) {
                        svg.current.removeChild(svg.current.lastChild);
                    }
                }
                svg.current.appendChild(mapDiagram.image)
            }
        }
    }, [mapDiagram]);


    // call refresh rules function from django then get new data
    const refreshRules = async () => {
        setLoading(true)
        setLoadingMessage("Refreshing rules")
        try {
            await usePost(window.location.href, { 'refresh_rules': true }, false)
            setLoadingMessage("Rules Refreshed. Getting Mapping Rules")
            window.location.reload(true)
        }
        catch (err) {
            console.log(err)
        }

    }
    // download map diagram
    const downloadImage = (img) => {
        setDownloadingImg(true);
        if (mapDiagram.image || img) {
          let svg2;
          if (img) {
            svg2 = img;
          } else {
            svg2 = mapDiagram.image;
          }
          var serializer = new XMLSerializer();
          var source = serializer.serializeToString(svg2);
          if (!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)) {
            source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
          }
          if (!source.match(/^<svg[^>]+"http\:\/\/www\.w3\.org\/1999\/xlink"/)) {
            source = source.replace(/^<svg/, '<svg xmlns:xlink="http://www.w3.org/1999/xlink"');
          }
          source = '<?xml version="1.0" standalone="no"?>\r\n' + source;
          var url = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(source);
          var element = document.createElement("a");
          element.download = "diagram.svg";
          element.href = url;
          element.click();
          element.remove();
          setDownloadingImg(false);
          downLoadingImgRef.current = false;
        } else {
          downLoadingImgRef.current = true;
        }
      };

    // apply destination table and source table filters to data
    const applyFilters = (variable) => {
        let newData = variable.map((scanreport) => scanreport);
        if (destinationTableFilter.length > 0) {
            newData = newData.filter((rule) => destinationTableFilter.includes(rule.destination_table.name));
        }
        if (sourceTableFilter.length > 0) {
            newData = newData.filter((rule) => sourceTableFilter.includes(rule.source_table.name));
        }
        return newData;
    };

    // if filter does not already exist, create a new destination table filter
    // and get a new map diagram
    const setDestinationFilter = (value) => {
        if (filters.find(filter => filter.name == value) == null) {
            setFilters(current => [...current, { title: "Destination Table:", name: value }])
            setDestinationTableFilter(current => [...current, value])
            
        }
    };
    // if filter does not already exist, create a new source table filter
    // and get a new map diagram
    const setSourceFilter = (value) => {
        if (filters.find(filter => filter.name == value) == null) {
            setFilters(current => [...current, { title: "Source Table:", name: value }])
            setSourceTableFilter(current => [...current, value])
            
        }

    };
    // remove a filter. Called inside concept tag
    const removeFilter = (title, name) => {
        setFilters(current => current.filter(filter => filter.name != name || filter.title != title))
        
        if (title.includes("Destination Table")) {
            setDestinationTableFilter(current => current.filter(filter => filter != name))
        }
        if (title.includes("Source Table")) {
            setSourceTableFilter(current => current.filter(filter => filter != name))
        }
    };

    if (loading) {
        //Render Loading State
        return (
            <div>
                <Flex padding="30px">
                    <Spinner />
                    <Flex marginLeft="10px">{loadingMessage ? loadingMessage : "Loading Mapping rules"}</Flex>
                </Flex>
            </div>
        )
    }
    return (
        <div >
            <MappingModal isOpen={isOpen} onOpen={onOpen} onClose={onClose}>
                <SummaryTbl values={values}
                    filters={filters} removeFilter={removeFilter} setDestinationFilter={setDestinationFilter} setSourceFilter={setSourceFilter}
                    destinationTableFilter={destinationTableFilter} sourceTableFilter={sourceTableFilter} />
            </MappingModal>
            <HStack my="10px">
                <Button variant="green" onClick={() => { refreshRules() }}>Refresh Rules</Button>
                <Button variant="blue" isLoading={isDownloading} loadingText="Downloading" spinnerPlacement="start" onClick={() => { window.downloadRules(setDownloading) }}>Download Mapping JSON</Button>
                <Button variant="yellow" onClick={() => { setMapDiagram(mapDiagram => ({ ...mapDiagram, showing: !mapDiagram.showing })) }}>{mapDiagram.showing ? "Hide " : "View "}Map Diagram</Button>
                <Button variant="red" isLoading={isDownloadingImg} loadingText="Downloading" spinnerPlacement="start" onClick={() => { downloadImage() }}>Download Map Diagram</Button>
                <Button variant="blue" isLoading={isDownloadingCSV} loadingText="Downloading" spinnerPlacement="start" onClick={() => { window.downloadCSV(setDownloadingCSV) }}>Download Mapping CSV</Button>
                <Button variant="blue" onClick={onOpen}>Show Summary view</Button>
            </HStack>

            <div>
                {mapDiagram.showing &&
                    <>
                        <div style={{ marginTop: '10px', marginBottom: '10px' }} ref={svg} />
                        {values.length > 0 ?
                            <>
                                {mapDiagram.image == null &&
                                    <Flex padding="30px">
                                        <Spinner />
                                        <Flex marginLeft="10px">Loading Map Diagram</Flex>
                                    </Flex>
                                }
                            </>
                            :
                            <Flex padding="30px">
                                <Flex marginLeft="10px">No Diagram to load</Flex>
                            </Flex>
                        }
                    </>
                }
            </div>
            {error ?
                <div>{error}</div>
                :
                <RulesTbl values={values}
                    filters={filters} removeFilter={removeFilter} setDestinationFilter={setDestinationFilter} setSourceFilter={setSourceFilter}
                    destinationTableFilter={destinationTableFilter} sourceTableFilter={sourceTableFilter} applyFilters={applyFilters} />

            }
        </div>
    );
}

export default MappingTbl;
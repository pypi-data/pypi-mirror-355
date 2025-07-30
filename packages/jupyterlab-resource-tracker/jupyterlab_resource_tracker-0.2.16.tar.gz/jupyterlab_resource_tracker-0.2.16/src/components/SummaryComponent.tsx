import React from 'react';
import { Paper, Typography } from '@mui/material';
import {
  DataGrid,
  GridColDef,
  GridFooterContainer,
  GridPagination,
  useGridApiContext,
  useGridSelector,
  gridFilteredSortedRowEntriesSelector,
  GridRenderCellParams
} from '@mui/x-data-grid';
import { Summary } from '../common/types';

interface SummaryComponentProps {
  summary: Summary[];
  loading: boolean;
}

const SummaryComponent: React.FC<SummaryComponentProps> = (
  props
): JSX.Element => {
  const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'project', headerName: 'Project', width: 115 },
    { field: 'podName', headerName: 'Username', width: 105 },
    { field: 'usage', headerName: 'Usage (Hours)', type: 'number', width: 120 },
    {
      field: 'cost',
      headerName: 'Cost',
      type: 'number',
      width: 80
    },
    { field: 'month', headerName: 'Month', width: 60, align: 'center' },
    { field: 'year', headerName: 'Year', width: 60, align: 'center' },
    {
      field: 'lastUpdate',
      headerName: 'Updated',
      width: 135,
      renderCell: (params: GridRenderCellParams) => {
        const raw = params.value;
        if (!raw || typeof raw !== 'string') {
          return '';
        }
        let iso = raw;
        // Truncate microseconds to milliseconds (keeping only 3 digits)
        iso = iso.replace(/(\.\d{3})\d+/, '$1');
        // Convert +00:00 offset to 'Z' for UTC
        if (iso.endsWith('+00:00')) {
          iso = iso.replace('+00:00', 'Z');
        }
        const date = new Date(iso);
        if (isNaN(date.getTime())) {
          return '';
        }
        return date.toLocaleString('en-US', {
          dateStyle: 'short',
          timeStyle: 'short'
        });
      }
    },
    {
      field: 'user_efs_cost',
      headerName: 'User EFS cost',
      type: 'number',
      width: 140
    },
    {
      field: 'project_efs_cost',
      headerName: 'Project EFS cost',
      type: 'number',
      width: 150
    }
  ];

  const paginationModel = { page: 0, pageSize: 10 };

  function CustomFooter() {
    const apiRef = useGridApiContext();
    const rows = useGridSelector(apiRef, gridFilteredSortedRowEntriesSelector);
    const totalComputeTime = rows.reduce(
      (sum, rowEntry) => sum + (rowEntry.model.usage ?? 0),
      0
    );
    const totalComputeCost = rows.reduce(
      (sum, rowEntry) => sum + (rowEntry.model.cost ?? 0),
      0
    );

    const totalUserStorageCost = rows.reduce(
      (sum, rowEntry) => sum + (rowEntry.model.user_efs_cost ?? 0),
      0
    );

    return (
      <GridFooterContainer>
        <div
          style={{
            width: '100%',
            display: 'flex',
            justifyContent: 'flex-start',
            gap: '1rem',
            paddingLeft: '1rem'
          }}
        >
          <Typography variant="subtitle2">
            <strong>Total Computed Time (Hours):</strong>{' '}
            {totalComputeTime.toFixed(2)}
          </Typography>
          <Typography variant="subtitle2">
            <strong>Total Computed Cost:</strong> {totalComputeCost.toFixed(2)}
          </Typography>
          <Typography variant="subtitle2">
            <strong>Total User EFS Cost:</strong>{' '}
            {totalUserStorageCost.toFixed(2)}
          </Typography>
          <GridPagination />
        </div>
      </GridFooterContainer>
    );
  }

  return (
    <React.Fragment>
      <Typography variant="h6" gutterBottom>
        Monthly costs and usages to date
      </Typography>
      <Paper sx={{ p: 2, boxShadow: 3, borderRadius: 2, mb: 2 }}>
        <DataGrid
          slots={{ footer: CustomFooter }}
          autoHeight
          rows={props.summary}
          columns={columns}
          loading={props.loading}
          initialState={{
            pagination: { paginationModel },
            columns: {
              columnVisibilityModel: {
                id: false
              }
            }
          }}
          pageSizeOptions={[10, 20, 30]}
          disableRowSelectionOnClick
          sx={{ border: 0 }}
        />
      </Paper>
    </React.Fragment>
  );
};

export default SummaryComponent;
